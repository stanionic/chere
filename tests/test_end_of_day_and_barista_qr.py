from datetime import datetime

from app.extensions import db
from app.models import Role, User, Merchant, Shop, Product, Category, PosOrder, BaristaOrder, OrderStatus


def _login_admin(client, email="admin@chere-global.org"):
    user = User.query.filter_by(email=email).first()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True


def test_barista_qrcode_route_returns_png(client):
    response = client.get("/events/barista/qrcode.png?size=220")
    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert len(response.data) > 500


def test_admin_end_of_day_report_lists_service_totals(client):
    role = Role(name="admin")
    db.session.add(role)
    db.session.flush()

    admin_user = User(
        full_name="Admin User",
        email="admin@chere-global.org",
        role_id=role.id,
        is_active_account=True,
    )
    admin_user.set_password("secret123")
    db.session.add(admin_user)
    db.session.flush()

    merchant = Merchant(user_id=admin_user.id, business_name="Demo Merchant")
    db.session.add(merchant)
    db.session.flush()

    shop = Shop(merchant_id=merchant.id, name="Demo Shop")
    db.session.add(shop)
    db.session.flush()

    category = Category(shop_id=shop.id, name="Beverages")
    db.session.add(category)
    db.session.flush()

    product = Product(
        shop_id=shop.id,
        category_id=category.id,
        name="Coffee",
        base_price=2500,
        stock_quantity=10,
    )
    db.session.add(product)
    db.session.flush()

    pos_order = PosOrder(
        order_number="POS-001",
        shop_id=shop.id,
        subtotal=2500,
        tax_amount=450,
        total_amount=2950,
        status=OrderStatus.PENDING,
        created_at=datetime(2026, 9, 1, 12, 0, 0),
    )
    db.session.add(pos_order)

    barista_order = BaristaOrder(
        order_number="BAR-001",
        customer_name="Jane Doe",
        total_amount=4000,
        created_at=datetime(2026, 9, 1, 13, 0, 0),
    )
    db.session.add(barista_order)

    db.session.commit()

    _login_admin(client, "admin@chere-global.org")

    response = client.get("/admin/end-of-day")
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "End of Day" in text
    assert "2026-09-01" in text
    assert "6,950" in text or "6950" in text
