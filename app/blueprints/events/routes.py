from flask import render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import current_user
from app.blueprints.events import events_bp
from app.models import Event, EventParticipant, Transaction
from app.extensions import db
from app.blueprints.events.forms import EventRegistrationForm, MoMoPaymentForm
from app.i18n import translate
from app.services.momo_service import momo_service
from datetime import datetime
from itsdangerous import URLSafeSerializer, BadSignature
from sqlalchemy import or_
import uuid


def _participant_token_serializer():
    return URLSafeSerializer(current_app.config["SECRET_KEY"], salt="event-participant")


def _build_participant_token(participant):
    return _participant_token_serializer().dumps(
        {"participant_id": participant.id, "event_id": participant.event_id}
    )


def _read_participant_token(token):
    if not token:
        return None
    try:
        payload = _participant_token_serializer().loads(token)
    except BadSignature:
        return None
    participant_id = payload.get("participant_id")
    event_id = payload.get("event_id")
    if not participant_id or not event_id:
        return None
    return payload


def _can_access_participant(participant, token=None):
    if current_user.is_authenticated and participant.email == current_user.email:
        return True
    payload = _read_participant_token(token)
    if not payload:
        return False
    return (
        payload.get("participant_id") == participant.id
        and payload.get("event_id") == participant.event_id
    )


def _find_registered_participant(event_id, token=None):
    if current_user.is_authenticated:
        return (
            EventParticipant.query.filter_by(event_id=event_id, email=current_user.email)
            .order_by(EventParticipant.registration_date.desc())
            .first()
        )

    payload = _read_participant_token(token)
    if not payload or payload.get("event_id") != event_id:
        return None

    return EventParticipant.query.filter_by(
        id=payload["participant_id"],
        event_id=event_id,
    ).first()


def _get_reserved_participant_count(event):
    return event.participants.filter(
        EventParticipant.status.in_(["pending", "confirmed"])
    ).count()


def _is_event_full(event, reserved_count=None):
    if not event.max_participants:
        return False
    if reserved_count is None:
        reserved_count = _get_reserved_participant_count(event)
    return reserved_count >= event.max_participants


@events_bp.route("/event/barista-coffee-experience")
def barista_experience():
    """Renders the full Barista app for the Barista Coffee Experience event."""
    event = Event.query.filter_by(slug="barista-coffee-experience", is_published=True).first_or_404()
    return render_template("events/barista_experience.html", event=event)


@events_bp.route("/")
def index():
    """Liste tous les événements publiés."""
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("q", "", type=str).strip()
    query = Event.query.filter_by(is_published=True)

    if search_query:
        like_pattern = f"%{search_query}%"
        query = query.filter(
            or_(
                Event.title.ilike(like_pattern),
                Event.summary.ilike(like_pattern),
                Event.description.ilike(like_pattern),
                Event.location.ilike(like_pattern),
                Event.event_type.ilike(like_pattern),
            )
        )

    events = query.order_by(Event.event_date.asc(), Event.created_at.desc()).paginate(
        page=page,
        per_page=12,
    )
    return render_template("events/index.html", events=events, search_query=search_query)


@events_bp.route("/event/<slug>")
def event_detail(slug):
    """Affiche les détails d'un événement."""
    event = Event.query.filter_by(slug=slug, is_published=True).first_or_404()
    form = EventRegistrationForm()
    
    # Vérifier si l'utilisateur est déjà inscrit
    participant = None
    if current_user.is_authenticated:
        participant = EventParticipant.query.filter_by(
            event_id=event.id,
            email=current_user.email
        ).first()
    reserved_count = _get_reserved_participant_count(event)
    is_full = _is_event_full(event, reserved_count)
    can_register = event.is_registration_open() and not is_full
    related_events = (
        Event.query.filter(
            Event.is_published.is_(True),
            Event.id != event.id,
            Event.event_type == event.event_type,
        )
        .order_by(Event.event_date.asc(), Event.created_at.desc())
        .limit(3)
        .all()
    )
    if not related_events:
        related_events = (
            Event.query.filter(
                Event.is_published.is_(True),
                Event.id != event.id,
            )
            .order_by(Event.event_date.asc(), Event.created_at.desc())
            .limit(3)
            .all()
        )

    return render_template(
        "events/event_detail.html",
        event=event,
        form=form,
        participant=participant,
        related_events=related_events,
        reserved_count=reserved_count,
        is_full=is_full,
        can_register=can_register,
    )


@events_bp.route("/event/<slug>/register", methods=["POST"])
def register_event(slug):
    """Enregistre un participant à un événement."""
    event = Event.query.filter_by(slug=slug, is_published=True).first_or_404()
    form = EventRegistrationForm()
    
    if not event.is_registration_open():
        return jsonify({
            "success": False,
            "error": translate("events.routes.registration_closed"),
        }), 400
    
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
                    "error": translate("events.routes.already_registered"),
                }), 400
            
            # Vérifier le nombre max de participants
            reserved_count = _get_reserved_participant_count(event)
            if _is_event_full(event, reserved_count):
                    return jsonify({
                        "success": False,
                        "error": translate("events.routes.event_full"),
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
                participant_token = _build_participant_token(participant)
                return jsonify({
                    "success": True,
                    "message": translate("events.routes.registration_confirmed"),
                    "redirect": url_for(
                        "events.event_registered",
                        event_id=participant.event_id,
                        token=participant_token,
                    ),
                })
            else:
                # Créer une transaction et rediriger vers le paiement
                db.session.commit()
                participant_token = _build_participant_token(participant)
                return jsonify({
                    "success": True,
                    "message": translate("events.routes.registration_recorded"),
                    "redirect": url_for(
                        "events.payment",
                        participant_id=participant.id,
                        token=participant_token,
                    ),
                })
                
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "success": False,
                "error": translate("events.routes.registration_error", error=str(e)),
            }), 500
    
    return jsonify({
        "success": False,
        "errors": form.errors
    }), 400


@events_bp.route("/payment/<int:participant_id>")
def payment(participant_id):
    """Page de paiement MoMo."""
    participant = EventParticipant.query.get_or_404(participant_id)
    event = participant.event
    form = MoMoPaymentForm()
    access_token = request.args.get("token", type=str)

    if not _can_access_participant(participant, access_token):
        flash(translate("events.routes.payment_access_denied"), "error")
        return redirect(url_for("events.index"))
    
    # Vérifier que l'événement est payant
    if not event.is_paid:
        flash(translate("events.routes.free_event"), "info")
        return redirect(
            url_for("events.event_registered", event_id=event.id, token=access_token)
        )
    
    return render_template(
        "events/payment.html",
        participant=participant,
        event=event,
        form=form,
        amount=event.price,
        participant_token=_build_participant_token(participant),
    )


@events_bp.route("/api/payment/initiate", methods=["POST"])
def initiate_payment():
    """Initie une demande de paiement MoMo."""
    data = request.get_json(silent=True) or {}
    participant_id = data.get("participant_id")
    phone_number = data.get("phone_number")
    access_token = data.get("token")
    
    participant = EventParticipant.query.get_or_404(participant_id)
    event = participant.event

    if not _can_access_participant(participant, access_token):
        return jsonify({
            "success": False,
            "error": translate("events.routes.access_denied"),
        }), 403
    
    if not event.is_paid:
        return jsonify({
            "success": False,
            "error": translate("events.routes.free_event_short"),
        }), 400
    
    # Valider le numéro
    if not momo_service.validate_phone_number(phone_number):
        return jsonify({
            "success": False,
            "error": translate("events.routes.invalid_phone"),
            "hint": translate("events.form.phone_format"),
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
                "message": translate("events.routes.payment_request_sent"),
                "reference_id": result.get("reference_id"),
                "transaction_id": transaction.id
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get("error", translate("events.routes.unknown_error")),
                "details": result.get("details")
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": translate("events.routes.payment_error", error=str(e)),
        }), 500


@events_bp.route("/api/payment/verify/<int:transaction_id>")
def verify_payment(transaction_id):
    """Vérifie le statut d'une transaction."""
    transaction = Transaction.query.get_or_404(transaction_id)
    access_token = request.args.get("token", type=str)

    if not _can_access_participant(transaction.participant, access_token):
        return jsonify({
            "success": False,
            "error": translate("events.routes.access_denied"),
        }), 403
    
    if not transaction.momo_reference:
        return jsonify({
            "success": False,
            "error": translate("events.routes.invalid_transaction"),
        }), 400
    
    try:
        # Vérifier le statut auprès de MoMo
        status_result = momo_service.get_transaction_status(transaction.momo_reference)
        
        if status_result.get("status") == "SUCCESSFUL":
            # Mettre à jour la transaction et le participant
            transaction.status = "success"
            transaction.paid_at = datetime.utcnow()
            
            participant = transaction.participant
            participant.status = "confirmed"
            participant.confirmation_date = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                "success": True,
                "status": "SUCCESSFUL",
                "message": translate("events.routes.payment_confirmed"),
                "redirect": url_for(
                    "events.event_registered",
                    event_id=transaction.event_id,
                    token=_build_participant_token(participant),
                ),
            })
        
        elif status_result.get("status") == "FAILED":
            transaction.status = "failed"
            db.session.commit()
            return jsonify({
                "success": False,
                "status": "FAILED",
                "message": translate("events.routes.payment_failed"),
                "error": status_result.get("error")
            }), 400
        
        else:
            # Still pending
            return jsonify({
                "success": False,
                "status": "PENDING",
                "message": translate("events.routes.payment_pending"),
            }), 202
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": translate("events.routes.verification_error", error=str(e)),
        }), 500


@events_bp.route("/event/<int:event_id>/registered")
def event_registered(event_id):
    """Page de confirmation d'inscription."""
    event = Event.query.get_or_404(event_id)
    participant = _find_registered_participant(
        event_id,
        token=request.args.get("token", type=str),
    )
    
    if not participant:
        flash(translate("events.routes.participant_not_found"), "error")
        return redirect(url_for("events.index"))
    
    return render_template(
        "events/registered.html",
        event=event,
        participant=participant
    )


@events_bp.route("/card")
def card():
    """Endpoint de compatibilité pour les anciennes URLs."""
    return redirect(url_for("events.index"))
