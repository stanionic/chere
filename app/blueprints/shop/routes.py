import uuid
from datetime import datetime

from flask import render_template, request, redirect, url_for, flash, jsonify, current_app, abort
from itsdangerous import URLSafeSerializer, BadSignature

from app.blueprints.shop import shop_bp
from app.blueprints.shop.forms import ShopCheckoutForm
from app.extensions import db
from app.models import ShopProduct, ShopOrder
from app.i18n import translate
from app.services.momo_service import momo_service


def _order_token_serializer():
    return URLSafeSerializer(current_app.config["SECRET_KEY"], salt="shop-order")


def _build_order_token(order):
    return _order_token_serializer().dumps({"order_id": order.id, "reference": order.reference})


def _read_order_token(token):
    if not token:
        return None
    try:
        payload = _order_token_serializer().loads(token)
    except BadSignature:
        return None
    if not payload.get("order_id") or not payload.get("reference"):
        return None
    return payload


def _get_order_for_visitor(order_id, token):
    """Retourne la commande si le token correspond (pas besoin de compte)."""
    order = ShopOrder.query.get(order_id)
    if not order:
        return None
    payload = _read_order_token(token)
    if not payload or payload.get("order_id") != order.id or payload.get("reference") != order.reference:
        return None
    return order


def slugify(value):
    """Slug simple pour les URLs produits (admin)."""
    import re
    import unicodedata
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value or "produit"


@shop_bp.route("/")
def index():
    """Catalogue public : produits publies par l'admin."""
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("q", "", type=str).strip()
    query = ShopProduct.query.filter_by(is_published=True)
    if search_query:
        like = f"%{search_query}%"
        query = query.filter(
            db.or_(ShopProduct.name.ilike(like), ShopProduct.description.ilike(like))
        )
    products = query.order_by(ShopProduct.created_at.desc()).paginate(page=page, per_page=12)
    return render_template("shop/index.html", products=products, search_query=search_query)


@shop_bp.route("/product/<slug>")
def product_detail(slug):
    """Page produit + bouton d'achat MoMo."""
    product = ShopProduct.query.filter_by(slug=slug, is_published=True).first_or_404()
    form = ShopCheckoutForm()
    related = (
        ShopProduct.query.filter(
            ShopProduct.is_published.is_(True),
            ShopProduct.id != product.id,
        )
        .order_by(ShopProduct.created_at.desc())
        .limit(4)
        .all()
    )
    return render_template(
        "shop/product_detail.html",
        product=product,
        form=form,
        related=related,
    )


@shop_bp.route("/product/<slug>/buy", methods=["POST"])
def buy(slug):
    """Cree une commande puis redirige vers le paiement MoMo."""
    product = ShopProduct.query.filter_by(slug=slug, is_published=True).first_or_404()
    form = ShopCheckoutForm()

    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            flash(errors[0], "danger")
        return redirect(url_for("shop.product_detail", slug=slug))

    quantity = form.quantity.data or 1

    # Verrou de stock : 0 = illimoite (cf. modele ShopProduct)
    if product.stock_quantity and quantity > product.stock_quantity:
        flash(translate("shop.checkout.insufficient_stock", stock=product.stock_quantity), "danger")
        return redirect(url_for("shop.product_detail", slug=slug))

    order = ShopOrder(
        reference=f"SHP-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}",
        product_id=product.id,
        customer_name=form.customer_name.data.strip(),
        customer_phone=momo_service.normalize_phone_number(form.customer_phone.data),
        quantity=quantity,
        unit_price=float(product.price),
        total_amount=float(product.price) * quantity,
        currency=product.currency or "RWF",
        status="pending",
    )
    db.session.add(order)
    db.session.commit()

    token = _build_order_token(order)
    return redirect(url_for("shop.checkout", order_id=order.id, token=token))


@shop_bp.route("/order/<int:order_id>/checkout")
def checkout(order_id):
    """Page de paiement MoMo d'une commande."""
    token = request.args.get("token", type=str)
    order = _get_order_for_visitor(order_id, token)
    if not order:
        abort(404)

    if order.status == "paid":
        return redirect(url_for("shop.order_status", order_id=order.id, token=token))

    return render_template(
        "shop/checkout.html",
        order=order,
        product=order.product,
        order_token=token,
    )


@shop_bp.route("/order/<int:order_id>")
def order_status(order_id):
    """Confirmation / suivi de commande."""
    token = request.args.get("token", type=str)
    order = _get_order_for_visitor(order_id, token)
    if not order:
        abort(404)
    return render_template("shop/order_status.html", order=order, order_token=token)


@shop_bp.route("/api/order/<int:order_id>/pay", methods=["POST"])
def initiate_payment(order_id):
    """Initie un Request-to-Pay MoMo pour la commande."""
    token = (request.get_json(silent=True) or {}).get("token") or request.form.get("token")
    order = _get_order_for_visitor(order_id, token)
    if not order:
        return jsonify({"success": False, "error": translate("shop.routes.not_found")}), 404

    if order.status == "paid":
        return jsonify({"success": False, "error": translate("shop.routes.already_paid")}), 400

    phone = request.get_json(silent=True) or {}
    phone_number = phone.get("phone_number") or order.customer_phone

    if not momo_service.validate_phone_number(phone_number):
        return jsonify({
            "success": False,
            "error": translate("shop.routes.invalid_phone"),
            "hint": translate("shop.checkout.momo_format"),
        }), 400

    # Actualise le numero saisi sur la commande
    order.customer_phone = momo_service.normalize_phone_number(phone_number)

    result = momo_service.request_to_pay(
        amount=order.total_amount,
        phone_number=order.customer_phone,
        external_id=f"shop_{order.id}_{uuid.uuid4().hex[:8]}",
        payer_message=f"Achat {order.product.name}",
        payee_note=f"Commande {order.reference}",
    )

    if result.get("success"):
        order.momo_reference = result.get("reference_id")
        order.status = "pending"
        order.response_data = result
        db.session.commit()
        return jsonify({
            "success": True,
            "message": translate("shop.routes.payment_request_sent"),
            "reference_id": result.get("reference_id"),
            "order_id": order.id,
        })

    order.status = "failed"
    order.response_data = result
    db.session.commit()
    return jsonify({
        "success": False,
        "error": result.get("error", translate("shop.routes.unknown_error")),
        "details": result.get("details"),
    }), 400


@shop_bp.route("/api/order/<int:order_id>/status")
def poll_payment(order_id):
    """Verifie le statut du paiement MoMo aupres de l'operateur."""
    token = request.args.get("token", type=str)
    order = _get_order_for_visitor(order_id, token)
    if not order:
        return jsonify({"success": False, "error": translate("shop.routes.not_found")}), 404

    if order.status == "paid":
        return jsonify({
            "success": True,
            "status": "SUCCESSFUL",
            "message": translate("shop.routes.payment_confirmed"),
        })

    if not order.momo_reference:
        return jsonify({"success": False, "error": translate("shop.routes.invalid_transaction")}), 400

    status_result = momo_service.get_transaction_status(order.momo_reference)
    remote_status = status_result.get("status")

    if remote_status == "SUCCESSFUL":
        order.status = "paid"
        order.paid_at = datetime.utcnow()
        # Debit le stock (0 = illimite)
        product = order.product
        if product.stock_quantity:
            product.stock_quantity = max(0, product.stock_quantity - order.quantity)
        db.session.commit()
        return jsonify({
            "success": True,
            "status": "SUCCESSFUL",
            "message": translate("shop.routes.payment_confirmed"),
            "redirect": url_for("shop.order_status", order_id=order.id, token=token),
        })

    if remote_status == "FAILED":
        order.status = "failed"
        db.session.commit()
        return jsonify({
            "success": False,
            "status": "FAILED",
            "message": translate("shop.routes.payment_failed"),
        }), 400

    return jsonify({
        "success": False,
        "status": "PENDING",
        "message": translate("shop.routes.payment_pending"),
    }), 202
