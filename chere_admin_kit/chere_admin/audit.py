import hashlib, json, datetime as dt
from flask import g, has_request_context, request
from flask_login import current_user
from .core import ctx

REDACT = {"password", "passwd", "token", "api_key", "apikey", "secret", "csrf_token", "authorization"}
LOGIN_FAIL_LIMIT, LOGIN_WINDOW_MIN = 5, 10


def redact(obj):
    if isinstance(obj, dict):
        return {k: "[REDACTED]" if k.lower() in REDACT else redact(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [redact(v) for v in obj]
    return obj


def audit(action, target=None, before=None, after=None, outcome="success", actor_id=None, commit=True):
    c = ctx()
    if actor_id is None and getattr(current_user, "is_authenticated", False):
        actor_id = current_user.id
    row = c.M.AuditLog(
        actor_id=actor_id, action=action, target=None if target is None else str(target)[:120],
        before=json.dumps(redact(before), default=str) if before is not None else None,
        after=json.dumps(redact(after), default=str) if after is not None else None,
        outcome=outcome,
        ip=(request.remote_addr if has_request_context() else None),
        correlation_id=getattr(g, "correlation_id", None) if has_request_context() else None)
    c.db.session.add(row)
    if commit:
        c.db.session.commit()
    return row


def _fingerprint(identifier):
    return hashlib.sha256(identifier.lower().encode()).hexdigest()[:12]   # no raw usernames/emails


def recent_failed_logins(identifier):
    c = ctx()
    since = dt.datetime.utcnow() - dt.timedelta(minutes=LOGIN_WINDOW_MIN)
    return c.M.AuditLog.query.filter(c.M.AuditLog.action == "login.failed",
                                     c.M.AuditLog.target == _fingerprint(identifier),
                                     c.M.AuditLog.ts >= since).count()


def is_locked_out(identifier):
    return recent_failed_logins(identifier) >= LOGIN_FAIL_LIMIT


def record_failed_login(identifier):
    """Call from CHERE's login route on a bad password. Raises an alert at the threshold."""
    fp = _fingerprint(identifier)
    audit("login.failed", target=fp, outcome="failure", actor_id=0)
    if recent_failed_logins(identifier) == LOGIN_FAIL_LIMIT:
        ctx().notifier.notify_security_event({"kind": "failed_logins", "ref": fp})
