"""RBAC: deny-by-default permission checks, escalation guards, module gating."""
from functools import wraps
from flask import abort, current_app, redirect, request, url_for
from flask_login import current_user


def _c():
    return current_app.extensions["chere_admin"]


PERMISSIONS = {
    "dashboard.view": "View admin dashboard",
    "users.view": "View users", "users.create": "Create users", "users.edit": "Edit users",
    "users.suspend": "Change account status", "users.delete": "Deactivate accounts",
    "roles.view": "View roles", "roles.manage": "Create/edit roles", "roles.assign": "Assign roles to users",
    "permissions.view": "View permission matrix", "permissions.manage": "Grant/deny per-user permissions",
    "modules.view": "View modules", "modules.manage": "Enable/disable modules",
    "settings.view": "View settings", "settings.manage": "Change settings",
    "audit_logs.view": "View audit log",
    "notifications.view": "View notification history", "notifications.manage": "Configure/test notifications",
}
HIGH_PRIVILEGE = {"roles.manage", "roles.assign", "permissions.manage", "settings.manage",
                  "users.delete", "notifications.manage", "modules.manage"}
_ALL = set(PERMISSIONS)
_VIEW = {p for p in PERMISSIONS if p.endswith(".view")}
DEFAULT_ROLES = {
    "super_admin": ("Super Administrator", _ALL),
    "admin": ("Administrator", _ALL - {"roles.manage", "permissions.manage", "settings.manage"}),
    "moderator": ("Moderator", {"dashboard.view", "users.view", "users.suspend", "audit_logs.view"}),
    "manager": ("Manager", {"dashboard.view", "users.view", "users.edit", "modules.view"}),
    "support_agent": ("Support Agent", {"dashboard.view", "users.view"}),
    "standard_user": ("Standard User", set()),
    "auditor": ("Read-Only Auditor", _VIEW),
}


def seed(c):
    db, M = c.db, c.M
    for code, desc in PERMISSIONS.items():
        if not M.Permission.query.filter_by(code=code).first():
            db.session.add(M.Permission(code=code, description=desc))
    db.session.flush()
    for slug, (name, codes) in DEFAULT_ROLES.items():
        role = M.Role.query.filter_by(slug=slug).first()
        if role is None:                       # never overwrite admin customisations
            role = M.Role(slug=slug, name=name, is_system=True)
            role.permissions = M.Permission.query.filter(M.Permission.code.in_(codes)).all() if codes else []
            db.session.add(role)
    db.session.commit()


def _active(user):
    return bool(user is not None and getattr(user, "is_authenticated", False)
                and getattr(user, "status", "active") == "active")


def effective_permissions(user):
    if not _active(user):
        return set()
    M = _c().M
    perms = set()
    for r in _roles(user):
        if r.is_active:
            perms |= {p.code for p in r.permissions}
    for o in M.Override.query.filter_by(user_id=user.id).all():
        (perms.add if o.granted else perms.discard)(o.permission.code)
    return perms


def _roles(user):
    c = _c()
    return (c.db.session.query(c.M.Role).join(c.M.user_roles, c.M.user_roles.c.role_id == c.M.Role.id)
            .filter(c.M.user_roles.c.user_id == user.id).all())


def user_roles(user):
    return _roles(user)


def has_perm(user, code):
    return code in effective_permissions(user)


def is_super(user):
    return _active(user) and any(r.slug == "super_admin" and r.is_active for r in _roles(user))


def can_grant(actor, code):
    """Actors may only hand out permissions they hold; super admins may grant any."""
    return is_super(actor) or (code not in HIGH_PRIVILEGE and has_perm(actor, code))


def active_super_admins(exclude_user_id=None):
    c = _c()
    q = (c.db.session.query(c.User).join(c.M.user_roles, c.M.user_roles.c.user_id == c.User.id)
         .join(c.M.Role, c.M.Role.id == c.M.user_roles.c.role_id)
         .filter(c.M.Role.slug == "super_admin", c.M.Role.is_active.is_(True),
                 c.User.status == "active"))
    if exclude_user_id is not None:
        q = q.filter(c.User.id != exclude_user_id)
    return q.count()


def require_permission(code):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **k):
            if not getattr(current_user, "is_authenticated", False):
                if request.accept_mimetypes.best == "application/json":
                    abort(401)
                login_view = getattr(getattr(current_app, "login_manager", None), "login_view", None)
                if not login_view:      # no configured login page -> plain 401 (Flask-Login default)
                    abort(401)
                return redirect(url_for(login_view, next=request.path))
            if not has_perm(current_user, code):
                from .audit import audit
                audit("access.denied", target=f"{request.method} {request.path}",
                      after={"needed": code}, outcome="failure")
                abort(403)
            return fn(*a, **k)
        return wrapper
    return deco


def module_enabled(name):
    row = _c().M.ModuleSetting.query.get(name)
    return True if row is None else row.enabled


def module_required(name):
    """Decorate CHERE routes so a disabled module is enforced on the server."""
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **k):
            if not module_enabled(name):
                abort(503, description=f"Module '{name}' is disabled")
            return fn(*a, **k)
        return wrapper
    return deco
