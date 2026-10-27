import os, sys, pytest, requests
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from demo_app import create_app
from chere_admin.rbac import seed


@pytest.fixture
def app(monkeypatch):
    for k in ("CALLMEBOT_API_KEY", "CALLMEBOT_PHONE", "CALLMEBOT_ENABLED"):
        monkeypatch.delenv(k, raising=False)
    a = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://", "WTF_CSRF_ENABLED": False,
                    "NOTIFY_SYNC": True, "NOTIFY_BACKOFF_BASE": 0})
    with a.app_context():
        seed(a.chere)
    yield a


from types import SimpleNamespace


def mk(app, name, role=None, status="active"):
    c = app.chere
    with app.app_context():
        u = app.User(username=name, email=f"{name}@x.io", password_hash=app.hash("pw"), status=status)
        app.db.session.add(u); app.db.session.commit()
        if role:
            r = c.M.Role.query.filter_by(slug=role).first()
            app.db.session.execute(c.M.user_roles.insert().values(user_id=u.id, role_id=r.id)); app.db.session.commit()
        return SimpleNamespace(id=u.id)


def role_id(app, slug):
    with app.app_context():
        return app.chere.M.Role.query.filter_by(slug=slug).first().id


def set_status(app, uid, status):
    with app.app_context():
        app.db.session.get(app.User, uid).status = status; app.db.session.commit()


def q(app, fn):
    with app.app_context():
        return fn(app.chere.M)


def login(app, name):
    cl = app.test_client()
    assert cl.post("/login", data={"username": name, "password": "pw"}).status_code == 200
    return cl


def enable_cmb(monkeypatch):
    monkeypatch.setenv("CALLMEBOT_ENABLED", "true"); monkeypatch.setenv("CALLMEBOT_PHONE", "+50948911268")
    monkeypatch.setenv("CALLMEBOT_API_KEY", "SECRETKEY123")


class Resp:
    def __init__(s, code=200, text="Message queued"): s.status_code, s.text = code, text


# ---------- authentication / authorization ----------
def test_anonymous_denied(app):
    cl = app.test_client()
    for p in ("/admin/", "/admin/users", "/admin/audit", "/admin/notifications", "/admin/roles"):
        assert cl.get(p).status_code in (302, 401)

def test_standard_user_denied_and_audited(app):
    mk(app, "bob", "standard_user"); cl = login(app, "bob")
    assert cl.get("/admin/users").status_code == 403
    assert q(app, lambda M: M.AuditLog.query.filter_by(action="access.denied", outcome="failure").count()) == 1

def test_role_limits_access(app):
    mk(app, "aud", "auditor"); cl = login(app, "aud")
    assert cl.get("/admin/audit").status_code == 200
    assert cl.post("/admin/users/1/status", data={"status": "suspended", "confirm": "yes"}).status_code == 403

def test_suspended_admin_loses_access(app):
    a = mk(app, "adm", "super_admin"); mk(app, "root2", "super_admin"); cl = login(app, "adm")
    assert cl.get("/admin/users").status_code == 200
    set_status(app, a.id, "suspended")
    assert cl.get("/admin/users").status_code == 403

# ---------- permission enforcement & escalation ----------
def test_grant_and_revoke_changes_backend_access(app):
    root = mk(app, "root", "super_admin"); u = mk(app, "sam", "standard_user")
    r, s = login(app, "root"), login(app, "sam")
    assert s.get("/admin/users").status_code == 403
    r.post(f"/admin/users/{u.id}/overrides", data={"permission": "users.view", "mode": "grant", "confirm": "yes"})
    assert s.get("/admin/users").status_code == 200
    r.post(f"/admin/users/{u.id}/overrides", data={"permission": "users.view", "mode": "clear", "confirm": "yes"})
    assert s.get("/admin/users").status_code == 403

def test_explicit_deny_override_beats_role(app):
    mk(app, "root", "super_admin"); u = mk(app, "ann", "support_agent")
    r, a = login(app, "root"), login(app, "ann")
    assert a.get("/admin/users").status_code == 200
    r.post(f"/admin/users/{u.id}/overrides", data={"permission": "users.view", "mode": "deny", "confirm": "yes"})
    assert a.get("/admin/users").status_code == 403

def test_no_self_escalation(app):
    mk(app, "root", "super_admin"); m = mk(app, "mod", "moderator")
    cl = login(app, "mod"); sa = SimpleNamespace(id=role_id(app, "super_admin"))
    assert cl.post(f"/admin/users/{m.id}/roles", data={"role_ids": [sa.id], "confirm": "yes"}).status_code == 403
    assert cl.post(f"/admin/users/{m.id}/overrides", data={"permission": "roles.manage", "mode": "grant", "confirm": "yes"}).status_code == 403

def test_admin_cannot_assign_super_admin_or_touch_one(app):
    root = mk(app, "root", "super_admin"); mk(app, "adm", "admin"); t = mk(app, "tgt", "standard_user")
    cl = login(app, "adm"); sa = SimpleNamespace(id=role_id(app, "super_admin"))
    assert cl.post(f"/admin/users/{t.id}/roles", data={"role_ids": [sa.id], "confirm": "yes"}).status_code == 403
    assert cl.post(f"/admin/users/{root.id}/status", data={"status": "suspended", "confirm": "yes"}).status_code == 403

def test_last_super_admin_protected(app):
    root = mk(app, "root", "super_admin"); other = mk(app, "r2", "super_admin")
    cl = login(app, "root")
    # remove the other one -> allowed (root remains)
    assert cl.post(f"/admin/users/{other.id}/status", data={"status": "suspended", "confirm": "yes"}).status_code == 302
    # now root is last: self-change blocked, and a second super admin that is suspended can't help
    assert cl.post(f"/admin/users/{root.id}/status", data={"status": "suspended", "confirm": "yes"}).status_code == 403
    set_status(app, other.id, "active")
    c2 = login(app, "r2")
    assert c2.post(f"/admin/users/{root.id}/roles", data={"role_ids": [], "confirm": "yes"}).status_code == 302  # allowed: r2 remains
    assert cl.get("/admin/users").status_code == 403   # root lost privileges
    assert c2.post(f"/admin/users/{other.id}/roles", data={"role_ids": [], "confirm": "yes"}).status_code == 403  # self

def test_confirmation_required(app):
    mk(app, "root", "super_admin"); u = mk(app, "u1", "standard_user"); cl = login(app, "root")
    assert cl.post(f"/admin/users/{u.id}/status", data={"status": "suspended"}).status_code == 400

def test_mass_assignment_ignored(app):
    mk(app, "root", "super_admin"); u = mk(app, "u1", "standard_user"); cl = login(app, "root")
    cl.post(f"/admin/users/{u.id}/status", data={"status": "suspended", "confirm": "yes", "id": 999, "password_hash": "x"})
    with app.app_context():
        row = app.db.session.get(app.User, u.id)
        assert row.status == "suspended" and row.password_hash != "x" and app.db.session.get(app.User, 999) is None

def test_disabled_module_enforced_on_server(app):
    mk(app, "root", "super_admin"); mk(app, "bob", "standard_user")
    r, b = login(app, "root"), login(app, "bob")
    assert b.get("/messaging").status_code == 200
    r.post("/admin/modules/messaging/toggle", data={"confirm": "yes"})
    assert b.get("/messaging").status_code == 503
    assert r.get("/admin/modules").status_code == 200       # admin recovery route still works

def test_audit_trail_records_changes_and_is_append_only(app):
    mk(app, "root", "super_admin"); u = mk(app, "u1", "standard_user"); cl = login(app, "root")
    cl.post(f"/admin/users/{u.id}/status", data={"status": "suspended", "confirm": "yes"})
    with app.app_context():
        row = app.chere.M.AuditLog.query.filter_by(action="user.status_changed").one()
        assert '"suspended"' in row.after and row.correlation_id
        row.outcome = "tampered"
        with pytest.raises(RuntimeError):
            app.db.session.commit()
        app.db.session.rollback()
        app.db.session.delete(app.chere.M.AuditLog.query.first())
        with pytest.raises(RuntimeError):
            app.db.session.commit()
        app.db.session.rollback()

def test_audit_redacts_secrets(app):
    from chere_admin.audit import redact
    assert redact({"password": "p", "nested": {"api_key": "k", "ok": 1}}) == {"password": "[REDACTED]", "nested": {"api_key": "[REDACTED]", "ok": 1}}

# ---------- CallMeBot ----------
def test_missing_credentials_safe(app):
    with app.app_context():
        assert app.chere.notifier.notify_new_user({"user_id": 5}).status == "skipped:not_configured"

def test_successful_send_uses_timeouts_and_hides_key(app, monkeypatch, caplog):
    enable_cmb(monkeypatch); seen = {}
    def fake(url, **kw): seen.update(kw); return Resp()
    monkeypatch.setattr(requests, "get", fake)
    caplog.set_level("DEBUG")
    with app.app_context():
        row = app.chere.notifier.notify_new_user({"user_id": 5})
        assert row.status == "sent" and seen["timeout"] and seen["params"]["phone"] == "+50948911268"
        assert "SECRETKEY123" not in caplog.text and "SECRETKEY123" not in (row.message + (row.error or ""))
        assert "password" not in row.message.lower()

def test_timeout_does_not_crash_and_is_retried_then_failed(app, monkeypatch):
    enable_cmb(monkeypatch); calls = []
    def boom(url, **kw): calls.append(1); raise requests.ConnectTimeout(f"{url}?apikey=SECRETKEY123")
    monkeypatch.setattr(requests, "get", boom)
    with app.app_context():
        row = app.chere.notifier.notify_critical_error({"error_id": "E1"})
        assert row.status == "failed" and row.attempts == 3 and len(calls) == 3
        assert "SECRETKEY123" not in row.error

def test_4xx_not_retried_and_retry_endpoint_works(app, monkeypatch):
    enable_cmb(monkeypatch)
    monkeypatch.setattr(requests, "get", lambda *a, **k: Resp(401, "bad key"))
    with app.app_context():
        row = app.chere.notifier.notify_critical_error({"error_id": "E2"})
        rid = row.id; assert row.status == "failed" and row.attempts == 1
    monkeypatch.setattr(requests, "get", lambda *a, **k: Resp())
    mk(app, "root", "super_admin"); cl = login(app, "root")
    cl.post(f"/admin/notifications/{rid}/retry")
    assert q(app, lambda M: M.NotificationLog.query.get(rid).status) == "sent"

def test_dedupe_and_rate_limit(app, monkeypatch):
    enable_cmb(monkeypatch); monkeypatch.setattr(requests, "get", lambda *a, **k: Resp())
    with app.app_context():
        n = app.chere.notifier
        assert n.notify_critical_error({"error_id": "same"}).status == "sent"
        assert n.notify_critical_error({"error_id": "same"}).status == "skipped:duplicate"
        n.put("notif.rate_limit_per_hour", 2); app.db.session.commit()
        n.notify_critical_error({"error_id": "b"})
        assert n.notify_critical_error({"error_id": "c"}).status == "skipped:rate_limited"

def test_event_toggle_and_min_severity(app, monkeypatch):
    enable_cmb(monkeypatch); monkeypatch.setattr(requests, "get", lambda *a, **k: Resp())
    with app.app_context():
        n = app.chere.notifier
        n.put("notif.evt.user.registered", "0"); app.db.session.commit()
        assert n.notify_new_user({"user_id": 1}).status == "skipped:disabled"
        n.put("notif.min_severity", "critical"); app.db.session.commit()
        assert n.notify_permission_change({"actor_id": 1, "action": "x"}).status == "skipped:below_min_severity"

def test_test_message_only_on_explicit_post_and_needs_permission(app, monkeypatch):
    enable_cmb(monkeypatch); sent = []
    monkeypatch.setattr(requests, "get", lambda *a, **k: sent.append(1) or Resp())
    mk(app, "aud", "auditor"); mk(app, "root", "super_admin")
    assert login(app, "aud").post("/admin/notifications/test", data={"confirm": "yes"}).status_code == 403
    assert not sent
    login(app, "root").post("/admin/notifications/test", data={"confirm": "yes"})
    assert len(sent) == 1

def test_bruteforce_lockout_and_single_alert(app, monkeypatch):
    enable_cmb(monkeypatch); sent = []
    monkeypatch.setattr(requests, "get", lambda *a, **k: sent.append(1) or Resp())
    mk(app, "vic"); cl = app.test_client()
    codes = [cl.post("/login", data={"username": "vic", "password": "nope"}).status_code for _ in range(7)]
    assert codes[:5] == [401] * 5 and codes[5:] == [429, 429]
    assert len(sent) == 1
    assert cl.post("/login", data={"username": "vic", "password": "pw"}).status_code == 429

# ---------- regression ----------
def test_existing_users_can_still_login(app):
    mk(app, "old"); assert login(app, "old")

def test_dashboard_shows_real_counts(app):
    mk(app, "root", "super_admin"); mk(app, "p1", status="pending"); mk(app, "s1", status="suspended")
    html = login(app, "root").get("/admin/").get_data(as_text=True)
    assert "Utilisateurs" in html and ">3<" in html.replace("</b>", "<").replace("<b>", ">")

def test_csrf_enforced_when_enabled():
    a = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://", "WTF_CSRF_ENABLED": True})
    cl = a.test_client()
    # any state-changing POST without a CSRF token is rejected (global CSRFProtect)
    assert cl.post("/admin/notifications/test", data={"confirm": "yes"}).status_code == 400
    assert cl.post("/login", data={"username": "x", "password": "y"}).status_code == 400
