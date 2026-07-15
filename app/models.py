"""
Modèles de données CHERE.
Couvre : utilisateurs/rôles, services, secteurs, projets, partenaires,
blog, équipe, statistiques, messages de contact, newsletter, médias.
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


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
    """Transactions de paiement MoMo pour les événements."""
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False, index=True)
    participant_id = db.Column(db.Integer, db.ForeignKey("event_participants.id"), nullable=False, index=True)
    
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
