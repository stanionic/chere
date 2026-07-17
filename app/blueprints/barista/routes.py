from flask import render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.blueprints.barista import barista_bp
from app.models import (
    Event, EventParticipant, Transaction, 
    BaristaMenu, BaristaOrder, BaristaOrderItem
)
from app.extensions import db
from app.services.momo_service import momo_service
from datetime import datetime
import uuid


@barista_bp.route("/")
def index():
    """Main Barista coffee ordering page."""
    # Get menu items grouped by category
    menu_items = BaristaMenu.query.filter_by(is_available=True).order_by(BaristaMenu.order).all()
    categories = {}
    for item in menu_items:
        if item.category not in categories:
            categories[item.category] = []
        categories[item.category].append(item)
    
    return render_template("barista/index.html", categories=categories, menu_items=menu_items)


@barista_bp.route("/event/<slug>")
def event_link(slug):
    """Link to Barista from an event (e.g., Barista Coffee Experience)."""
    event = Event.query.filter_by(slug=slug).first_or_404()
    return redirect(url_for("barista.index", event_id=event.id))


@barista_bp.route("/api/menu")
def get_menu():
    """Get the barista menu as JSON (for frontend)."""
    menu_items = BaristaMenu.query.filter_by(is_available=True).order_by(BaristaMenu.order).all()
    categories = {}
    for item in menu_items:
        if item.category not in categories:
            categories[item.category] = []
        categories[item.category].append({
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "price": item.price,
            "icon": item.icon,
        })
    return jsonify({"success": True, "categories": categories})


@barista_bp.route("/order", methods=["POST"])
def create_order():
    """Create a new coffee order."""
    data = request.json
    
    # Parse cart
    cart = data.get("cart", [])
    if not cart:
        return jsonify({"success": False, "error": "Le panier est vide"}), 400
    
    customer_name = data.get("customer_name")
    if not customer_name:
        return jsonify({"success": False, "error": "Veuillez entrer votre nom"}), 400
    
    customer_email = data.get("customer_email")
    customer_phone = data.get("customer_phone")
    event_id = data.get("event_id")
    
    try:
        # Calculate total
        total = 0.0
        order_items_data = []
        for item in cart:
            menu_item = BaristaMenu.query.get(item["menu_item_id"])
            if not menu_item or not menu_item.is_available:
                return jsonify({"success": False, "error": f"Item {item.get('name')} is no longer available"}), 400
            subtotal = menu_item.price * item.get("quantity", 1)
            total += subtotal
            order_items_data.append({
                "menu_item": menu_item,
                "quantity": item.get("quantity", 1),
                "special_requests": item.get("special_requests", "")
            })
        
        # Create order
        order_number = f"CH-COF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"
        order = BaristaOrder(
            order_number=order_number,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            total_amount=total,
            status="pending",
            event_id=event_id
        )
        db.session.add(order)
        db.session.flush()
        
        # Add order items
        for item_data in order_items_data:
            order_item = BaristaOrderItem(
                order_id=order.id,
                menu_item_id=item_data["menu_item"].id,
                menu_item_name=item_data["menu_item"].name,
                price=item_data["menu_item"].price,
                quantity=item_data["quantity"],
                special_requests=item_data["special_requests"]
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Commande créée avec succès",
            "order_id": order.id,
            "order_number": order_number,
            "total_amount": total
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la création de la commande: {str(e)}"
        }), 500


@barista_bp.route("/order/<int:order_id>")
def order_detail(order_id):
    """Show order detail page."""
    order = BaristaOrder.query.get_or_404(order_id)
    return render_template("barista/confirm.html", order=order)


@barista_bp.route("/order/<int:order_id>/payment")
def order_payment(order_id):
    """Payment page for coffee order."""
    order = BaristaOrder.query.get_or_404(order_id)
    
    if order.status == "paid":
        flash("Commande déjà payée", "info")
        return redirect(url_for("barista.order_detail", order_id=order.id))
    
    return render_template("barista/payment.html", order=order)


@barista_bp.route("/api/order/<int:order_id>/payment/initiate", methods=["POST"])
def initiate_order_payment(order_id):
    """Initiate MoMo payment for a coffee order."""
    order = BaristaOrder.query.get_or_404(order_id)
    data = request.json
    phone_number = data.get("phone_number")
    
    if not momo_service.validate_phone_number(phone_number):
        return jsonify({
            "success": False,
            "error": "Numéro de téléphone invalide",
            "hint": "Format: +250 7xx xxx xxx ou 07xx xxx xxx"
        }), 400
    
    try:
        external_id = f"cof_{order.id}_{uuid.uuid4().hex[:8]}"
        
        result = momo_service.request_to_pay(
            amount=order.total_amount,
            phone_number=phone_number,
            external_id=external_id,
            payer_message=f"Commande {order.order_number}",
            payee_note=f"Client: {order.customer_name}"
        )
        
        if result.get("success"):
            transaction = Transaction(
                amount=order.total_amount,
                phone_number=momo_service.normalize_phone_number(phone_number),
                status="pending"
            )
            if order.event_id:
                transaction.event_id = order.event_id
            db.session.add(transaction)
            db.session.flush()
            
            order.transaction_id = transaction.id
            order.status = "pending"
            transaction.momo_reference = result.get("reference_id")
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


@barista_bp.route("/api/order/payment/verify/<int:transaction_id>")
def verify_order_payment(transaction_id):
    """Verify payment status for a coffee order."""
    transaction = Transaction.query.get_or_404(transaction_id)
    order = BaristaOrder.query.filter_by(transaction_id=transaction_id).first()
    
    if not order:
        return jsonify({"success": False, "error": "Commande non trouvée"}), 400
        
    if not transaction.momo_reference:
        return jsonify({"success": False, "error": "Pas de référence MoMo"}), 400
    
    try:
        result = momo_service.get_transaction_status(transaction.momo_reference)
        
        if result.get("success"):
            status = result.get("status")
            
            if status == "SUCCESSFUL":
                transaction.status = "success"
                transaction.paid_at = datetime.utcnow()
                order.status = "paid"
                db.session.commit()
                
                return jsonify({
                    "success": True,
                    "status": "paid",
                    "message": "Paiement confirmé! Commande validée.",
                    "redirect": url_for("barista.order_detail", order_id=order.id)
                })
            elif status == "FAILED":
                transaction.status = "failed"
                order.status = "pending"
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
