import datetime as dt
from sqlalchemy import event, UniqueConstraint


def utcnow():
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


def define_models(db, user_table):
    # Idempotent: the same `db` (and its MetaData) may be shared across several
    # create_app() calls (e.g. per-test app fixtures). Redefining the tables or
    # models would raise "Table is already defined", so cache them on the db.
    cache = getattr(db, "_chere_admin_models_cache", None)
    if cache is not None and cache[0] == user_table:
        return cache[1]

    role_perms = db.Table(
        "admin_role_permissions",
        db.Column("role_id", db.Integer, db.ForeignKey("admin_role.id"), primary_key=True),
        db.Column("permission_id", db.Integer, db.ForeignKey("admin_permission.id"), primary_key=True))
    user_roles = db.Table(
        "admin_user_roles",
        db.Column("user_id", db.Integer, db.ForeignKey(f"{user_table}.id"), primary_key=True),
        db.Column("role_id", db.Integer, db.ForeignKey("admin_role.id"), primary_key=True))

    class Permission(db.Model):
        __tablename__ = "admin_permission"
        id = db.Column(db.Integer, primary_key=True)
        code = db.Column(db.String(80), unique=True, nullable=False)
        description = db.Column(db.String(200), default="")

    class Role(db.Model):
        __tablename__ = "admin_role"
        id = db.Column(db.Integer, primary_key=True)
        slug = db.Column(db.String(60), unique=True, nullable=False)
        name = db.Column(db.String(80), nullable=False)
        description = db.Column(db.String(200), default="")
        is_active = db.Column(db.Boolean, default=True, nullable=False)
        is_system = db.Column(db.Boolean, default=False, nullable=False)
        permissions = db.relationship(Permission, secondary=role_perms, lazy="selectin")

    class Override(db.Model):
        __tablename__ = "admin_user_override"
        __table_args__ = (UniqueConstraint("user_id", "permission_id"),)
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey(f"{user_table}.id"), nullable=False)
        permission_id = db.Column(db.Integer, db.ForeignKey("admin_permission.id"), nullable=False)
        granted = db.Column(db.Boolean, nullable=False)   # True=grant, False=explicit deny
        permission = db.relationship(Permission, lazy="joined")

    class AuditLog(db.Model):
        __tablename__ = "admin_audit_log"
        id = db.Column(db.Integer, primary_key=True)
        ts = db.Column(db.DateTime, default=utcnow, index=True, nullable=False)
        actor_id = db.Column(db.Integer, index=True)
        action = db.Column(db.String(80), index=True, nullable=False)
        target = db.Column(db.String(120))
        before = db.Column(db.Text)
        after = db.Column(db.Text)
        outcome = db.Column(db.String(12), index=True, default="success")
        ip = db.Column(db.String(45))
        correlation_id = db.Column(db.String(64))

    def _immutable(*_a, **_k):
        raise RuntimeError("Audit records are append-only.")
    event.listen(AuditLog, "before_update", _immutable)
    event.listen(AuditLog, "before_delete", _immutable)

    class Setting(db.Model):
        __tablename__ = "admin_setting"
        key = db.Column(db.String(80), primary_key=True)
        value = db.Column(db.String(200))

    class ModuleSetting(db.Model):
        __tablename__ = "admin_module_setting"
        name = db.Column(db.String(60), primary_key=True)
        enabled = db.Column(db.Boolean, default=True, nullable=False)

    class NotificationLog(db.Model):
        __tablename__ = "admin_notification_log"
        id = db.Column(db.Integer, primary_key=True)
        ts = db.Column(db.DateTime, default=utcnow, index=True, nullable=False)
        event = db.Column(db.String(60), index=True)
        severity = db.Column(db.String(10))
        message = db.Column(db.String(500))
        status = db.Column(db.String(40), index=True)   # queued|sent|failed|skipped:<why>
        attempts = db.Column(db.Integer, default=0)
        error = db.Column(db.String(200))
        dedupe_key = db.Column(db.String(120), index=True)

    from types import SimpleNamespace
    models = SimpleNamespace(Permission=Permission, Role=Role, Override=Override,
                             AuditLog=AuditLog, Setting=Setting, ModuleSetting=ModuleSetting,
                             NotificationLog=NotificationLog, role_perms=role_perms,
                             user_roles=user_roles)
    db._chere_admin_models_cache = (user_table, models)
    return models
