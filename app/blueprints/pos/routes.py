"""
POS Blueprint for CHERE events
- Register POS devices
- Manage products
- Manage orders
"""
import random
import string
from datetime import datetime
from flask import request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import (
    POSDevice, Product, ProductVariant, 
    PosOrder, PosOrderItem, OrderStatus, 
    Category, Merchant, Shop, AuditLog,
    PaymentMethod, TransactionStatus, PosTransaction
)
from app.blueprints.pos import pos_bp


def _generate_order_number():
    return "CH-POS-" + "".join(random.choices(string.digits, k=8))


SUPPORTED_MODELS = {"sunmi_p2_pro", "pax_a920_pro", "newland_n950"}


@pos_bp.route("/devices/register", methods=["POST"])
@login_required
def register_device():
    data = request.get_json(force=True, silent=True) or {}
    model = data.get("device_model")
    serial = data.get("device_serial")
    shop_id = data.get("shop_id")

    if model not in SUPPORTED_MODELS:
        return jsonify({"error": f"Modèle non supporté. Modèles valides: {sorted(SUPPORTED_MODELS)}"}), 400
    if not serial or not shop_id:
        return jsonify({"error": "device_serial et shop_id sont requis"}), 400

    existing = POSDevice.query.filter_by(device_serial=serial).first()
    if existing:
        return jsonify({"message": "Terminal déjà enregistré", "device": existing.to_dict()})

    device = POSDevice(
        shop_id=shop_id,
        device_serial=serial,
        device_model=model,
        device_name=data.get("device_name"),
        is_online=True,
        last_sync_at=datetime.utcnow(),
    )
    db.session.add(device)
    db.session.commit()

    return jsonify({"message": "Terminal enregistré", "device": device.to_dict()}), 201


@pos_bp.route("/devices/<int:device_id>/pending-orders", methods=["GET"])
@login_required
def pending_orders(device_id):
    device = POSDevice.query.get_or_404(device_id)
    orders = PosOrder.query.filter_by(
        shop_id=device.shop_id, status=OrderStatus.PENDING
    ).order_by(PosOrder.created_at.asc()).all()
    return jsonify([o.to_dict() for o in orders])


@pos_bp.route("/devices/<int:device_id>/sync", methods=["POST"])
@login_required
def sync_device(device_id):
    device = POSDevice.query.get_or_404(device_id)
    data = request.get_json(force=True, silent=True) or {}
    offline_orders = data.get("orders", [])

    synced = []
    for offline_order in offline_orders:
        order = PosOrder(
            order_number=offline_order.get("offline_id", "OFFLINE"),
            shop_id=device.shop_id,
            pos_device_id=device.id,
            status=OrderStatus.DRAFT,
        )
        subtotal = 0
        for item in offline_order.get("items", []):
            product = Product.query.get(item.get("product_id"))
            if not product:
                continue
            quantity = int(item.get("quantity", 1))
            unit_price = product.effective_price
            line_total = unit_price * quantity
            subtotal += line_total
            order.items.append(PosOrderItem(
                product_id=product.id, quantity=quantity,
                unit_price=unit_price, line_total=line_total,
            ))
        order.subtotal = subtotal
        order.total_amount = subtotal
        db.session.add(order)
        synced.append(order)

    device.is_online = True
    device.last_sync_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "message": f"{len(synced)} commande(s) synchronisée(s)",
        "orders": [o.to_dict() for o in synced],
    })


@pos_bp.route("/devices/<int:device_id>/heartbeat", methods=["POST"])
@login_required
def heartbeat(device_id):
    device = POSDevice.query.get_or_404(device_id)
    device.is_online = True
    device.last_sync_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "ok"})


# Products
@pos_bp.route("/products/categories", methods=["GET"])
@login_required
def get_categories():
    shop_id = request.args.get("shop_id")
    query = Category.query
    if shop_id:
        query = query.filter_by(shop_id=shop_id)
    categories = query.all()
    return jsonify([
        {"id": c.id, "name": c.name, "shop_id": c.shop_id}
        for c in categories
    ])


@pos_bp.route("/products", methods=["GET"])
@login_required
def list_products():
    shop_id = request.args.get("shop_id")
    category_id = request.args.get("category_id")

    query = Product.query.filter_by(is_active=True)
    if shop_id:
        query = query.filter_by(shop_id=shop_id)
    if category_id:
        query = query.filter_by(category_id=category_id)

    products = query.order_by(Product.name).all()
    return jsonify([p.to_dict() for p in products])


@pos_bp.route("/products/<int:product_id>", methods=["GET"])
@login_required
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())


# Orders
@pos_bp.route("/orders", methods=["POST"])
@login_required
def create_order():
    data = request.get_json(force=True, silent=True) or {}
    shop_id = data.get("shop_id")
    items_data = data.get("items", [])

    if not shop_id or not items_data:
        return jsonify({"error": "shop_id et items sont requis"}), 400

    order = PosOrder(
        order_number=_generate_order_number(),
        shop_id=shop_id,
        customer_id=current_user.id if current_user.is_authenticated else None,
        status=OrderStatus.DRAFT,
    )

    subtotal = 0
    for item in items_data:
        product = Product.query.get(item.get("product_id"))
        if not product:
            return jsonify({"error": f"Produit introuvable: {item.get('product_id')}"}), 404
        quantity = int(item.get("quantity", 1))
        if product.stock_quantity < quantity:
            return jsonify({"error": f"Stock insuffisant pour {product.name}"}), 409

        unit_price = product.effective_price
        line_total = unit_price * quantity
        subtotal += line_total

        order.items.append(PosOrderItem(
            product_id=product.id,
            variant_id=item.get("variant_id"),
            quantity=quantity,
            unit_price=unit_price,
            line_total=line_total,
        ))
        product.stock_quantity -= quantity

    tax_rate = 0.18
    tax_amount = round(float(subtotal) * tax_rate, 2)
    order.subtotal = subtotal
    order.tax_amount = tax_amount
    order.total_amount = float(subtotal) + tax_amount

    db.session.add(order)
    db.session.commit()

    if current_user.is_authenticated:
        AuditLog.record(
            current_user.id,
            "order.create",
            "pos_order",
            order.id,
            request.remote_addr
        )

    return jsonify({"message": "Commande créée", "order": order.to_dict()}), 201


@pos_bp.route("/orders/<int:order_id>", methods=["GET"])
@login_required
def get_order(order_id):
    order = PosOrder.query.get_or_404(order_id)
    return jsonify(order.to_dict())


@pos_bp.route("/orders/<int:order_id>/status", methods=["PATCH"])
@login_required
def update_order_status(order_id):
    order = PosOrder.query.get_or_404(order_id)
    data = request.get_json(force=True, silent=True) or {}
    new_status_value = data.get("status")

    try:
        new_status = OrderStatus(new_status_value)
    except ValueError:
        return jsonify({"error": "Statut invalide"}), 400

    try:
        order.transition_to(new_status)
    except ValueError as e:
        return jsonify({"error": str(e)}), 409

    db.session.commit()

    if current_user.is_authenticated:
        AuditLog.record(
            current_user.id,
            "order.status_change",
            "pos_order",
            order.id,
            request.remote_addr,
            details=new_status.value
        )

    return jsonify({"message": "Statut mis à jour", "order": order.to_dict()})


@pos_bp.route("/orders/shop/<int:shop_id>", methods=["GET"])
@login_required
def list_shop_orders(shop_id):
    status_filter = request.args.get("status")
    query = PosOrder.query.filter_by(shop_id=shop_id)
    if status_filter:
        try:
            query = query.filter_by(status=OrderStatus(status_filter))
        except ValueError:
            return jsonify({"error": "Statut invalide"}), 400
    orders = query.order_by(PosOrder.created_at.desc()).limit(100).all()
    return jsonify([o.to_dict() for o in orders])
