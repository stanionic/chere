"""
Modèles de données CHERE.
Couvre : utilisateurs/rôles, services, secteurs, projets, partenaires,
blog, équipe, statistiques, messages de contact, newsletter, médias,
événements, barista, et CHER Smart POS (caisse).
"""
import enum
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


# --- POS Enums
class UserRole(enum.Enum):
    ADMIN = "admin"
    MERCHANT_OWNER = "merchant_owner"
    CASHIER = "cashier"
    CUSTOMER = "customer"
    EVENT_ORGANIZER = "event_organizer"


class OrderStatus(enum.Enum):
    DRAFT = "brouillon"
    PENDING = "en_attente"
    PAYMENT_REQUESTED = "paiement_demande"
    PAYMENT_RECEIVED = "paiement_recu"
    PREPARING = "preparation"
    SHIPPED = "expediee"
    DELIVERED = "livree"
    CANCELLED = "annulee"
    REFUNDED = "remboursee"


class PaymentMethod(enum.Enum):
    MTN_MOMO = "mtn_momo"
    AIRTEL_MONEY = "airtel_money"
    CARD = "carte_bancaire"
    QR_CODE = "qr_code"
    NFC = "nfc"
    PAYMENT_LINK = "lien_paiement"


class TransactionStatus(enum.Enum):
    INITIATED = "initiee"
    PENDING = "en_attente"
    SUCCESS = "reussie"
    FAILED = "echouee"
    REFUNDED = "remboursee"


ALLOWED_TRANSITIONS = {
    OrderStatus.DRAFT: {OrderStatus.PENDING, OrderStatus.CANCELLED},
    OrderStatus.PENDING: {OrderStatus.PAYMENT_REQUESTED, OrderStatus.CANCELLED},
    OrderStatus.PAYMENT_REQUESTED: {OrderStatus.PAYMENT_RECEIVED, OrderStatus.CANCELLED},
    OrderStatus.PAYMENT_RECEIVED: {OrderStatus.PREPARING, OrderStatus.REFUNDED},
    OrderStatus.PREPARING: {OrderStatus.SHIPPED, OrderStatus.REFUNDED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED, OrderStatus.REFUNDED},
    OrderStatus.DELIVERED: {OrderStatus.REFUNDED},
    OrderStatus.CANCELLED: set(),
    OrderStatus.REFUNDED: set(),
}


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # admin, editor, viewer
    users = db.relationship("User", backref="role", lazy=True)

    def __repr__(self):
        return f"<Role {self.name}>"


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    is_active_account = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    notifications = db.relationship(
        "UserNotification",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.is_active_account

    def has_role(self, role_name):
        return self.role and self.role.name == role_name

    def unread_notification_count(self):
        return self.notifications.filter_by(is_read=False).count()

    def __repr__(self):
        return f"<User {self.email}>"


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    recipients = db.relationship(
        "UserNotification",
        back_populates="notification",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )


class UserNotification(db.Model):
    __tablename__ = "user_notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    notification_id = db.Column(db.Integer, db.ForeignKey("notifications.id"), nullable=False, index=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    user = db.relationship("User", back_populates="notifications")
    notification = db.relationship("Notification", back_populates="recipients")


class Sector(db.Model):
    """Secteurs d'intervention (Agriculture, Santé, Technologie, ...)."""
    __tablename__ = "sectors"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    icon = db.Column(db.String(60), nullable=False)  # classe Bootstrap Icons
    short_description = db.Column(db.String(240))
    order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)


class PillarIcon(db.Model):
    """Icônes représentant les sous-thèmes des 3 piliers (Innovation, Énergie, Humanitaire)."""
    __tablename__ = "pillar_icons"
    id = db.Column(db.Integer, primary_key=True)
    pillar = db.Column(db.String(30), nullable=False)  # innovation | renewable | humanitarian
    label = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(60), nullable=False)
    order = db.Column(db.Integer, default=0)


class Service(db.Model):
    __tablename__ = "services"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    slug = db.Column(db.String(160), unique=True, nullable=False)
    icon = db.Column(db.String(60), nullable=False)
    summary = db.Column(db.String(280))
    content = db.Column(db.Text)
    pillar = db.Column(db.String(30))  # innovation | renewable | humanitarian
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(180), unique=True, nullable=False)
    country = db.Column(db.String(100))
    continent = db.Column(db.String(60))  # Africa, Europe, Asia, Americas, Oceania
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    status = db.Column(db.String(30), default="coming_soon")  # coming_soon, ongoing, completed
    pillar = db.Column(db.String(30))
    summary = db.Column(db.String(280))
    content = db.Column(db.Text)
    cover_image = db.Column(db.String(255))
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Partner(db.Model):
    __tablename__ = "partners"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    logo = db.Column(db.String(255))
    website_url = db.Column(db.String(255))
    category = db.Column(db.String(60))  # ONU, ONG, Université, Entreprise, Institution, Banque
    order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)


class TeamMember(db.Model):
    __tablename__ = "team_members"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(140), nullable=False)
    role_title = db.Column(db.String(140))
    photo = db.Column(db.String(255))
    bio = db.Column(db.Text)
    linkedin_url = db.Column(db.String(255))
    order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)


class Article(db.Model):
    __tablename__ = "articles"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    category = db.Column(db.String(60))  # Innovation, Énergie, Humanitaire, Technologie
    excerpt = db.Column(db.String(300))
    content = db.Column(db.Text, nullable=False)
    cover_image = db.Column(db.String(255))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = db.relationship("User")
    is_published = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Statistic(db.Model):
    """Compteurs animés d'impact (Countries, Projects, People Empowered, ...)."""
    __tablename__ = "statistics"
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(120), nullable=False)
    value = db.Column(db.Integer, nullable=False, default=0)
    suffix = db.Column(db.String(10), default="")  # +, %, etc.
    icon = db.Column(db.String(60))
    order = db.Column(db.Integer, default=0)


class Message(db.Model):
    """Messages soumis via le formulaire de contact."""
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(140), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(200))
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class NewsletterSubscriber(db.Model):
    __tablename__ = "newsletter_subscribers"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)


class MediaAsset(db.Model):
    """Bibliothèque de médias utilisée par l'admin (images, illustrations)."""
    __tablename__ = "media_assets"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    alt_text = db.Column(db.String(200))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Event(db.Model):
    """Événements publics (conférences, ateliers, formations, etc.)."""
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(280))
    event_type = db.Column(db.String(50), nullable=False)  # conference, workshop, training, webinar, meetup, etc.
    is_paid = db.Column(db.Boolean, default=False)
    price = db.Column(db.Float, default=0.0)  # RWF
    currency = db.Column(db.String(3), default="RWF")
    max_participants = db.Column(db.Integer)  # NULL = unlimited
    location = db.Column(db.String(255))
    event_date = db.Column(db.DateTime)
    event_end_date = db.Column(db.DateTime)
    registration_deadline = db.Column(db.DateTime)
    cover_image = db.Column(db.String(255))
    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    organizer = db.relationship("User", foreign_keys=[organizer_id])
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    participants = db.relationship(
        "EventParticipant",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    transactions = db.relationship(
        "Transaction",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def get_participant_count(self):
        return self.participants.filter_by(status="confirmed").count()

    def is_registration_open(self):
        from datetime import datetime as dt
        if self.registration_deadline:
            return dt.utcnow() < self.registration_deadline
        return True

    def __repr__(self):
        return f"<Event {self.title}>"


class EventParticipant(db.Model):
    """Participants aux événements."""
    __tablename__ = "event_participants"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False, index=True)
    full_name = db.Column(db.String(140), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(30), default="pending")  # pending, confirmed, cancelled, no_show
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    confirmation_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    # Relationships
    event = db.relationship("Event", back_populates="participants")
    transaction = db.relationship("Transaction", uselist=False, back_populates="participant")

    __table_args__ = (
        db.Index("idx_event_email", "event_id", "email"),
    )

    def __repr__(self):
        return f"<EventParticipant {self.full_name} - {self.event.title}>"


class Transaction(db.Model):
    """Transactions de paiement MoMo pour les événements et barista."""
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=True, index=True)
    participant_id = db.Column(db.Integer, db.ForeignKey("event_participants.id"), nullable=True, index=True)
    
    # Payment Details
    amount = db.Column(db.Float, nullable=False)  # RWF
    currency = db.Column(db.String(3), default="RWF")
    phone_number = db.Column(db.String(20), nullable=False)  # MoMo phone
    
    # Transaction Status
    status = db.Column(db.String(30), default="pending")  # pending, success, failed, cancelled
    momo_reference = db.Column(db.String(100))  # Reference from MoMo API
    payment_method = db.Column(db.String(50), default="momo")  # momo, card, bank_transfer, etc.
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    
    # Response Data
    response_data = db.Column(db.JSON)  # Store full MoMo API response
    
    # Relationships
    event = db.relationship("Event", back_populates="transactions")
    participant = db.relationship("EventParticipant", back_populates="transaction")

    def is_paid(self):
        return self.status == "success"

    def __repr__(self):
        return f"<Transaction {self.id} - {self.status}>"


class BaristaMenu(db.Model):
    """Coffee menu items for the Barista experience."""
    __tablename__ = "barista_menu_items"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # espresso, cappuccino, latte, tea, pastry
    description = db.Column(db.String(255))
    price = db.Column(db.Float, nullable=False, default=0.0)  # RWF
    currency = db.Column(db.String(3), default="RWF")
    icon = db.Column(db.String(20))  # emoji
    is_available = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<BaristaMenu {self.name}>"


class BaristaOrder(db.Model):
    """Coffee order for the Barista experience."""
    __tablename__ = "barista_orders"
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(140), nullable=False)
    customer_email = db.Column(db.String(150))
    customer_phone = db.Column(db.String(20))
    status = db.Column(db.String(30), default="pending")  # pending, paid, preparing, ready, delivered
    total_amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default="RWF")
    
    # MoMo payment
    transaction_id = db.Column(db.Integer, db.ForeignKey("transactions.id"))
    transaction = db.relationship("Transaction", foreign_keys=[transaction_id])
    
    # If linked to an event
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"))
    event = db.relationship("Event", foreign_keys=[event_id])
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship(
        "BaristaOrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __repr__(self):
        return f"<BaristaOrder {self.order_number}>"


class BaristaOrderItem(db.Model):
    """Item in a Barista order."""
    __tablename__ = "barista_order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("barista_orders.id"), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("barista_menu_items.id"), nullable=False)
    menu_item_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    special_requests = db.Column(db.String(255))
    
    # Relationships
    order = db.relationship("BaristaOrder", back_populates="items")
    menu_item = db.relationship("BaristaMenu")
    
    def __repr__(self):
        return f"<BaristaOrderItem {self.menu_item_name} x{self.quantity}>"


# --- CHER Smart POS Models
class Merchant(db.Model):
    __tablename__ = "merchants"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    business_name = db.Column(db.String(150), nullable=False)
    business_registration_no = db.Column(db.String(80), nullable=True)
    country = db.Column(db.String(80), default="Rwanda")
    wallet_balance = db.Column(db.Numeric(14, 2), default=0)
    qr_code_permanent = db.Column(db.String(255), unique=True, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = db.relationship("User", backref="merchant", uselist=False)
    shops = db.relationship("Shop", back_populates="merchant", cascade="all, delete-orphan")
    cashiers = db.relationship("MerchantCashier", back_populates="merchant", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "business_name": self.business_name,
            "country": self.country,
            "wallet_balance": str(self.wallet_balance),
            "qr_code_permanent": self.qr_code_permanent,
            "is_verified": self.is_verified,
        }
    
    def __repr__(self):
        return f"<Merchant {self.business_name}>"


class Shop(db.Model):
    __tablename__ = "shops"
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchants.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=True)  # Link to Events!
    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    merchant = db.relationship("Merchant", back_populates="shops")
    event = db.relationship("Event", backref="shops")
    products = db.relationship("Product", back_populates="shop", cascade="all, delete-orphan")
    pos_devices = db.relationship("POSDevice", back_populates="shop", cascade="all, delete-orphan")
    orders = db.relationship("PosOrder", back_populates="shop", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Shop {self.name}>"


class MerchantCashier(db.Model):
    """Association entre un commerçant et ses caissiers (utilisateurs avec rôle CASHIER)."""
    __tablename__ = "merchant_cashiers"
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchants.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assigned_shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    merchant = db.relationship("Merchant", back_populates="cashiers")
    user = db.relationship("User", backref="cashier_assignments")
    assigned_shop = db.relationship("Shop")
    
    def __repr__(self):
        return f"<MerchantCashier {self.user.full_name} at {self.merchant.business_name}>"


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    
    products = db.relationship("Product", back_populates="category")
    parent = db.relationship("Category", remote_side=[id])
    
    def __repr__(self):
        return f"<Category {self.name}>"


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    barcode = db.Column(db.String(64), unique=True, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    base_price = db.Column(db.Numeric(12, 2), nullable=False)
    promo_price = db.Column(db.Numeric(12, 2), nullable=True)
    promo_active = db.Column(db.Boolean, default=False)
    stock_quantity = db.Column(db.Integer, default=0)
    low_stock_threshold = db.Column(db.Integer, default=5)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    shop = db.relationship("Shop", back_populates="products")
    category = db.relationship("Category", back_populates="products")
    variants = db.relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    
    @property
    def is_low_stock(self) -> bool:
        return self.stock_quantity <= self.low_stock_threshold
    
    @property
    def effective_price(self):
        return self.promo_price if (self.promo_active and self.promo_price is not None) else self.base_price
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "barcode": self.barcode,
            "base_price": str(self.base_price),
            "effective_price": str(self.effective_price),
            "stock_quantity": self.stock_quantity,
            "is_low_stock": self.is_low_stock,
            "is_active": self.is_active,
        }
    
    def __repr__(self):
        return f"<Product {self.name}>"


class ProductVariant(db.Model):
    __tablename__ = "product_variants"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price_delta = db.Column(db.Numeric(12, 2), default=0)
    stock_quantity = db.Column(db.Integer, default=0)
    
    product = db.relationship("Product", back_populates="variants")
    
    def __repr__(self):
        return f"<ProductVariant {self.name} for {self.product.name}>"


class PosOrder(db.Model):
    __tablename__ = "pos_orders"
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(30), unique=True, nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    pos_device_id = db.Column(db.Integer, db.ForeignKey("pos_devices.id"), nullable=True)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.DRAFT, nullable=False)
    subtotal = db.Column(db.Numeric(14, 2), default=0)
    tax_amount = db.Column(db.Numeric(14, 2), default=0)
    total_amount = db.Column(db.Numeric(14, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    shop = db.relationship("Shop", back_populates="orders")
    customer = db.relationship("User")
    pos_device = db.relationship("POSDevice", back_populates="orders")
    items = db.relationship("PosOrderItem", back_populates="order", cascade="all, delete-orphan")
    transactions = db.relationship("PosTransaction", back_populates="order")
    
    def can_transition_to(self, new_status: OrderStatus) -> bool:
        return new_status in ALLOWED_TRANSITIONS.get(self.status, set())
    
    def transition_to(self, new_status: OrderStatus):
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Transition invalide: {self.status.value} -> {new_status.value}"
            )
        self.status = new_status
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            "id": self.id,
            "order_number": self.order_number,
            "status": self.status.value,
            "subtotal": str(self.subtotal),
            "tax_amount": str(self.tax_amount),
            "total_amount": str(self.total_amount),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "items": [item.to_dict() for item in self.items],
        }
    
    def __repr__(self):
        return f"<PosOrder {self.order_number}>"


class PosOrderItem(db.Model):
    __tablename__ = "pos_order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("pos_orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey("product_variants.id"), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    line_total = db.Column(db.Numeric(14, 2), nullable=False)
    
    order = db.relationship("PosOrder", back_populates="items")
    product = db.relationship("Product")
    variant = db.relationship("ProductVariant")
    
    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": str(self.unit_price),
            "line_total": str(self.line_total),
        }
    
    def __repr__(self):
        return f"<PosOrderItem {self.product.name} x{self.quantity}>"


class POSDevice(db.Model):
    __tablename__ = "pos_devices"
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False)
    device_serial = db.Column(db.String(80), unique=True, nullable=False)
    device_model = db.Column(db.String(50), nullable=False)
    device_name = db.Column(db.String(100), nullable=True)
    is_online = db.Column(db.Boolean, default=False)
    last_sync_at = db.Column(db.DateTime, nullable=True)
    app_version = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    shop = db.relationship("Shop", back_populates="pos_devices")
    orders = db.relationship("PosOrder", back_populates="pos_device")
    
    def to_dict(self):
        return {
            "id": self.id,
            "device_serial": self.device_serial,
            "device_model": self.device_model,
            "is_online": self.is_online,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
        }
    
    def __repr__(self):
        return f"<POSDevice {self.device_serial}>"


class PosTransaction(db.Model):
    __tablename__ = "pos_transactions"
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(40), unique=True, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("pos_orders.id"), nullable=False)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchants.id"), nullable=False)
    method = db.Column(db.Enum(PaymentMethod), nullable=False)
    status = db.Column(db.Enum(TransactionStatus), default=TransactionStatus.INITIATED)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    currency = db.Column(db.String(10), default="RWF")
    provider_transaction_id = db.Column(db.String(120), nullable=True)
    provider_raw_response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    order = db.relationship("PosOrder", back_populates="transactions")
    merchant = db.relationship("Merchant")
    
    def to_dict(self):
        return {
            "id": self.id,
            "reference": self.reference,
            "order_id": self.order_id,
            "method": self.method.value,
            "status": self.status.value,
            "amount": str(self.amount),
            "currency": self.currency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
    
    def __repr__(self):
        return f"<PosTransaction {self.reference}>"


class AuditLog(db.Model):
    """Journal d'audit: trace toute action sensible pour la sécurité et la conformité."""
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.String(36), nullable=True)  # To support both integer and string IDs
    ip_address = db.Column(db.String(45), nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship("User")
    
    @staticmethod
    def record(user_id, action, entity_type=None, entity_id=None, ip_address=None, details=None):
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            ip_address=ip_address,
            details=details,
        )
        db.session.add(log)
        return log
    
    def __repr__(self):
        return f"<AuditLog {self.action} at {self.created_at}>"
