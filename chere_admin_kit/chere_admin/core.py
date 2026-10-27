"""Entry point: init_admin(app, db, User) wires the admin panel into an existing Flask app."""
import uuid
from types import SimpleNamespace
from flask import current_app, g, request
from flask_wtf.csrf import CSRFProtect


def ctx():
    return current_app.extensions["chere_admin"]


def init_admin(app, db, User, *, url_prefix="/admin", modules=None):
    from .models import define_models
    from .notifications import Notifier
    from .rbac import seed
    from .views import bp

    c = SimpleNamespace(db=db, User=User, modules=dict(modules or {}))
    c.M = define_models(db, User.__tablename__)
    c.notifier = Notifier(app, c)
    app.extensions["chere_admin"] = c

    if "csrf" not in app.extensions:          # reuse host CSRF if it already has one
        CSRFProtect(app)
    app.register_blueprint(bp, url_prefix=url_prefix)

    @app.before_request
    def _corr_id():
        g.correlation_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex

    @app.after_request
    def _hdr(resp):
        resp.headers["X-Request-ID"] = getattr(g, "correlation_id", "")
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        return resp

    @app.cli.command("admin-seed")
    def _seed_cmd():
        """Create default permissions and roles (idempotent)."""
        seed(c)
        print("RBAC seeded.")

    return c
