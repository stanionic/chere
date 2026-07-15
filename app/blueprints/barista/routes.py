from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.blueprints.barista import barista_bp
from app.models import Event, EventParticipant, Transaction
from app.extensions import db
from app.blueprints.barista.forms import EventRegistrationForm, MoMoPaymentForm
from app.services.momo_service import momo_service
from datetime import datetime
import uuid


@barista_bp.route("/")
def index():
    """Liste tous les événements publiés."""
    page = request.args.get("page", 1, type=int)
    events = Event.query.filter_by(is_published=True).paginate(page=page, per_page=12)
    return render_template("barista/index.html", events=events)


@barista_bp.route("/event/<slug>")
def event_detail(slug):
    """Affiche les détails d'un événement."""
    event = Event.query.filter_by(slug=slug).first_or_404()
    form = EventRegistrationForm()
    
    # Vérifier si l'utilisateur est déjà inscrit
    participant = None
    if current_user.is_authenticated:
        participant = EventParticipant.query.filter_by(
            event_id=event.id,
            email=current_user.email
        ).first()
    
    return render_template(
        "barista/event_detail.html",
        event=event,
        form=form,
        participant=participant
    )


@barista_bp.route("/event/<slug>/register", methods=["POST"])
def register_event(slug):
    """Enregistre un participant à un événement."""
    event = Event.query.filter_by(slug=slug).first_or_404()
    form = EventRegistrationForm()
    
    if not event.is_registration_open():
        return jsonify({"success": False, "error": "Les inscriptions sont fermées"}), 400
    
    if form.validate_on_submit():
        try:
            # Vérifier les doublons
            existing = EventParticipant.query.filter_by(
                event_id=event.id,
                email=form.email.data
            ).first()
            
            if existing:
                return jsonify({
                    "success": False,
                    "error": "Vous êtes déjà inscrit à cet événement"
                }), 400
            
            # Vérifier le nombre max de participants
            if event.max_participants:
                participant_count = event.get_participant_count()
                if participant_count >= event.max_participants:
                    return jsonify({
                        "success": False,
                        "error": "L'événement est complet"
                    }), 400
            
            # Créer le participant
            participant = EventParticipant(
                event_id=event.id,
                full_name=form.full_name.data,
                email=form.email.data,
                phone=form.phone.data,
                status="pending" if event.is_paid else "confirmed"
            )
            db.session.add(participant)
            db.session.flush()
            
            # Si gratuit, confirmer immédiatement
            if not event.is_paid:
                participant.status = "confirmed"
                participant.confirmation_date = datetime.utcnow()
                db.session.commit()
                return jsonify({
                    "success": True,
                    "message": "Inscription confirmée!",
                    "redirect": url_for("barista.event_registered", event_id=participant.event_id)
                })
            else:
                # Créer une transaction et rediriger vers le paiement
                db.session.commit()
                return jsonify({
                    "success": True,
                    "message": "Inscription enregistrée. Procédez au paiement.",
                    "redirect": url_for("barista.payment", participant_id=participant.id)
                })
                
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "success": False,
                "error": f"Erreur lors de l'inscription: {str(e)}"
            }), 500
    
    return jsonify({
        "success": False,
        "errors": form.errors
    }), 400


@barista_bp.route("/payment/<int:participant_id>")
def payment(participant_id):
    """Page de paiement MoMo."""
    participant = EventParticipant.query.get_or_404(participant_id)
    event = participant.event
    form = MoMoPaymentForm()
    
    # Vérifier que l'événement est payant
    if not event.is_paid:
        flash("Cet événement est gratuit", "info")
        return redirect(url_for("barista.event_registered", event_id=event.id))
    
    return render_template(
        "barista/payment.html",
        participant=participant,
        event=event,
        form=form,
        amount=event.price
    )


@barista_bp.route("/api/payment/initiate", methods=["POST"])
def initiate_payment():
    """Initie une demande de paiement MoMo."""
    data = request.json
    participant_id = data.get("participant_id")
    phone_number = data.get("phone_number")
    
    participant = EventParticipant.query.get_or_404(participant_id)
    event = participant.event
    
    if not event.is_paid:
        return jsonify({"success": False, "error": "Événement gratuit"}), 400
    
    # Valider le numéro
    if not momo_service.validate_phone_number(phone_number):
        return jsonify({
            "success": False,
            "error": "Numéro de téléphone invalide",
            "hint": "Format: +250 7xx xxx xxx ou 07xx xxx xxx"
        }), 400
    
    try:
        # Générer un ID externe unique
        external_id = f"evt_{event.id}_par_{participant.id}_{uuid.uuid4().hex[:8]}"
        
        # Appeler l'API MoMo
        result = momo_service.request_to_pay(
            amount=event.price,
            phone_number=phone_number,
            external_id=external_id,
            payer_message=f"Inscription {event.title}",
            payee_note=f"Participant: {participant.full_name}"
        )
        
        if result.get("success"):
            # Créer/Mettre à jour la transaction
            transaction = Transaction.query.filter_by(participant_id=participant_id).first()
            
            if not transaction:
                transaction = Transaction(
                    event_id=event.id,
                    participant_id=participant_id,
                    amount=event.price,
                    phone_number=momo_service.normalize_phone_number(phone_number),
                    status="pending"
                )
                db.session.add(transaction)
            
            transaction.momo_reference = result.get("reference_id")
            transaction.status = "pending"
            transaction.response_data = result
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Demande de paiement envoyée. Vérifiez votre téléphone.",
                "reference_id": result.get("reference_id"),
                "transaction_id": transaction.id
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get("error", "Erreur inconnue"),
                "details": result.get("details")
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@barista_bp.route("/api/payment/verify/<int:transaction_id>")
def verify_payment(transaction_id):
    """Vérifie le statut d'une transaction."""
    transaction = Transaction.query.get_or_404(transaction_id)
    
    if not transaction.momo_reference:
        return jsonify({"success": False, "error": "Pas de référence MoMo"}), 400
    
    try:
        # Vérifier le statut auprès de MoMo
        result = momo_service.get_transaction_status(transaction.momo_reference)
        
        if result.get("success"):
            status = result.get("status")
            
            if status == "SUCCESSFUL":
                # Mettre à jour la transaction et le participant
                transaction.status = "success"
                transaction.paid_at = datetime.utcnow()
                transaction.participant.status = "confirmed"
                transaction.participant.confirmation_date = datetime.utcnow()
                db.session.commit()
                
                return jsonify({
                    "success": True,
                    "status": "paid",
                    "message": "Paiement confirmé! Inscription validée.",
                    "redirect": url_for("barista.event_registered", event_id=transaction.event_id)
                })
            elif status == "FAILED":
                transaction.status = "failed"
                db.session.commit()
                
                return jsonify({
                    "success": False,
                    "status": "failed",
                    "error": "Paiement refusé"
                }), 400
            else:  # PENDING
                return jsonify({
                    "success": True,
                    "status": "pending",
                    "message": "Paiement en attente..."
                })
        else:
            return jsonify({
                "success": False,
                "error": "Impossible de vérifier le statut"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@barista_bp.route("/event/<int:event_id>/registered")
def event_registered(event_id):
    """Page de confirmation d'inscription."""
    event = Event.query.get_or_404(event_id)
    
    # Récupérer le dernier participant inscrit (de la session ou de l'utilisateur)
    participant = EventParticipant.query.filter_by(event_id=event_id).order_by(
        EventParticipant.registration_date.desc()
    ).first()
    
    if not participant:
        flash("Aucune inscription trouvée", "error")
        return redirect(url_for("barista.index"))
    
    return render_template("barista/registered.html", event=event, participant=participant)


@barista_bp.route("/api/payment/callback", methods=["POST"])
def payment_callback():
    """Webhook MoMo — appelé par MTN lors d'un changement de statut."""
    data = request.json or {}
    reference_id = data.get("referenceId")

    if reference_id:
        transaction = Transaction.query.filter_by(momo_reference=reference_id).first()
        if transaction:
            status = data.get("status", "").upper()
            if status == "SUCCESSFUL":
                transaction.status = "success"
                transaction.paid_at = datetime.utcnow()
                transaction.participant.status = "confirmed"
                transaction.participant.confirmation_date = datetime.utcnow()
            elif status == "FAILED":
                transaction.status = "failed"
            transaction.response_data = data
            db.session.commit()

    momo_service.handle_payment_callback(data)
    return jsonify({"success": True}), 200


@barista_bp.route("/card")
def card():
    """Page de carte pour compatibilité avec l'ancienne URL."""
    return render_template("barista/card.html")
