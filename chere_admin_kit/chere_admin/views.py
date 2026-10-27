from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import func
from .audit import audit
from .core import ctx
from .notifications import EVENTS, SEVERITY
from .rbac import (PERMISSIONS, active_super_admins, can_grant, effective_permissions, has_perm,
                   is_super, require_permission, user_roles)

bp = Blueprint("chere_admin", __name__, template_folder="templates")
STATUSES = {"active", "pending", "suspended", "deactivated"}
SORTABLE = {"id", "username", "email", "status", "created_at"}


@bp.app_context_processor
def _inject():
    return {"has_perm": lambda code: has_perm(current_user, code), "PERMISSIONS": PERMISSIONS}


@bp.route("/login-required")
def login_required_redirect():
    return redirect(url_for("admin.login"))


def _back(endpoint="chere_admin.dashboard", **kw):
    return redirect(url_for(endpoint, **kw))


def _need_confirm():
    if request.form.get("confirm") != "yes":
        abort(400, description="Confirmation required")


def _guard_target(target):
    """Common rules for changing another account."""
    if target.id == current_user.id:
        abort(403, description="You cannot modify your own privileges or status")
    if is_super(target) and not is_super(current_user):
        abort(403, description="Only a Super Administrator can modify a Super Administrator")


@bp.route("/")
@require_permission("dashboard.view")
def dashboard():
    c = ctx(); U = c.User
    rows = dict(c.db.session.query(U.status, func.count(U.id)).group_by(U.status).all())
    admins = (c.db.session.query(func.count(func.distinct(c.M.user_roles.c.user_id)))
              .join(c.M.Role, c.M.Role.id == c.M.user_roles.c.role_id)
              .filter(c.M.Role.slug.in_(["super_admin", "admin"])).scalar())
    stats = {"total": sum(rows.values()), "active": rows.get("active", 0), "pending": rows.get("pending", 0),
             "suspended": rows.get("suspended", 0), "admins": admins}
    events = c.M.AuditLog.query.order_by(c.M.AuditLog.id.desc()).limit(10).all()
    failed = c.M.NotificationLog.query.filter_by(status="failed").count()
    return render_template("chere_admin/dashboard.html", stats=stats, events=events, failed=failed)


@bp.route("/users")
@require_permission("users.view")
def users():
    c = ctx(); U = c.User
    q = request.args.get("q", "").strip()[:80]
    status = request.args.get("status", "")
    sort = request.args.get("sort", "id"); sort = sort if sort in SORTABLE else "id"
    desc = request.args.get("dir") == "desc"
    stmt = c.db.select(U)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(U.username.ilike(like) | U.email.ilike(like))
    if status in STATUSES:
        stmt = stmt.where(U.status == status)
    col = getattr(U, sort)
    stmt = stmt.order_by(col.desc() if desc else col.asc())
    page = c.db.paginate(stmt, page=request.args.get("page", 1, type=int), per_page=20, error_out=False)
    return render_template("chere_admin/users.html", page=page, q=q, status=status, STATUSES=sorted(STATUSES))


@bp.route("/users/<int:uid>")
@require_permission("users.view")
def user_detail(uid):
    c = ctx(); u = c.User.query.get_or_404(uid)
    logs = c.M.AuditLog.query.filter((c.M.AuditLog.actor_id == uid) | (c.M.AuditLog.target == f"user:{uid}")) \
        .order_by(c.M.AuditLog.id.desc()).limit(20).all()
    return render_template("chere_admin/user_detail.html", u=u, roles=user_roles(u),
                           all_roles=c.M.Role.query.filter_by(is_active=True).all(),
                           overrides=c.M.Override.query.filter_by(user_id=uid).all(),
                           effective=sorted(effective_permissions(u)), logs=logs, STATUSES=sorted(STATUSES))


@bp.route("/users/<int:uid>/status", methods=["POST"])
@require_permission("users.suspend")
def user_status(uid):
    c = ctx(); u = c.User.query.get_or_404(uid)
    _need_confirm(); _guard_target(u)
    new = request.form.get("status", "")
    if new not in STATUSES:
        abort(400)
    if new != "active" and is_super(u) and active_super_admins(exclude_user_id=u.id) == 0:
        abort(409, description="Cannot disable the last active Super Administrator")
    old, u.status = u.status, new
    audit("user.status_changed", f"user:{uid}", {"status": old}, {"status": new}, commit=False)
    c.db.session.commit()
    c.notifier.send_whatsapp_notification(
        f"CHERE ADMIN — Statut de compte modifié. Utilisateur: {uid}. Nouveau statut: {new}.",
        "account.status_changed", "warning", f"status:{uid}:{new}")
    flash("Status updated."); return _back("chere_admin.user_detail", uid=uid)


@bp.route("/users/<int:uid>/roles", methods=["POST"])
@require_permission("roles.assign")
def user_set_roles(uid):
    c = ctx(); u = c.User.query.get_or_404(uid)
    _need_confirm(); _guard_target(u)
    wanted_ids = {int(x) for x in request.form.getlist("role_ids") if x.isdigit()}
    wanted = c.M.Role.query.filter(c.M.Role.id.in_(wanted_ids)).all() if wanted_ids else []
    current = user_roles(u)
    changed = {r.id for r in wanted} ^ {r.id for r in current}
    mine = effective_permissions(current_user)
    for r in c.M.Role.query.filter(c.M.Role.id.in_(changed)).all() if changed else []:
        if r.slug == "super_admin" and not is_super(current_user):
            abort(403, description="Only a Super Administrator manages that role")
        if not is_super(current_user) and not {p.code for p in r.permissions} <= mine:
            abort(403, description="You cannot assign a role more powerful than your own")
    removing_super = any(r.slug == "super_admin" for r in current) and not any(r.slug == "super_admin" for r in wanted)
    if removing_super and active_super_admins(exclude_user_id=u.id) == 0:
        abort(409, description="Cannot remove the last active Super Administrator")
    before = [r.slug for r in current]
    c.db.session.execute(c.M.user_roles.delete().where(c.M.user_roles.c.user_id == uid))
    for r in wanted:
        c.db.session.execute(c.M.user_roles.insert().values(user_id=uid, role_id=r.id))
    audit("user.roles_changed", f"user:{uid}", {"roles": before}, {"roles": [r.slug for r in wanted]}, commit=False)
    c.db.session.commit()
    c.notifier.notify_permission_change({"actor_id": current_user.id, "action": f"roles de l'utilisateur {uid}"})
    if any(r.slug in ("super_admin", "admin") for r in wanted) and changed:
        c.notifier.send_whatsapp_notification(f"CHERE ADMIN — Nouvel administrateur: utilisateur {uid}.",
                                              "admin.created", "critical", f"admin:{uid}")
    flash("Roles updated."); return _back("chere_admin.user_detail", uid=uid)


@bp.route("/users/<int:uid>/overrides", methods=["POST"])
@require_permission("permissions.manage")
def user_override(uid):
    c = ctx(); u = c.User.query.get_or_404(uid)
    _need_confirm(); _guard_target(u)
    code, mode = request.form.get("permission", ""), request.form.get("mode", "")
    perm = c.M.Permission.query.filter_by(code=code).first()
    if not perm or mode not in {"grant", "deny", "clear"}:
        abort(400)
    if mode == "grant" and not can_grant(current_user, code):
        abort(403, description="You cannot grant a permission you do not hold")
    o = c.M.Override.query.filter_by(user_id=uid, permission_id=perm.id).first()
    before = None if o is None else ("grant" if o.granted else "deny")
    if mode == "clear":
        if o: c.db.session.delete(o)
    elif o:
        o.granted = mode == "grant"
    else:
        c.db.session.add(c.M.Override(user_id=uid, permission_id=perm.id, granted=mode == "grant"))
    audit("user.override_changed", f"user:{uid}", {code: before}, {code: mode}, commit=False)
    c.db.session.commit()
    c.notifier.notify_permission_change({"actor_id": current_user.id, "action": f"permission {code} ({mode}) pour {uid}"})
    flash("Permission override saved."); return _back("chere_admin.user_detail", uid=uid)


@bp.route("/roles")
@require_permission("roles.view")
def roles():
    c = ctx()
    rs = c.M.Role.query.order_by(c.M.Role.id).all()
    return render_template("chere_admin/roles.html", roles=rs, perms=sorted(PERMISSIONS),
                           matrix={r.id: {p.code for p in r.permissions} for r in rs})


@bp.route("/roles", methods=["POST"])
@require_permission("roles.manage")
def role_create():
    c = ctx(); name = request.form.get("name", "").strip()[:80]
    slug = "".join(ch if ch.isalnum() else "_" for ch in name.lower()).strip("_")[:60]
    if not slug or c.M.Role.query.filter_by(slug=slug).first():
        abort(400, description="Invalid or duplicate role name")
    c.db.session.add(c.M.Role(slug=slug, name=name, description=request.form.get("description", "")[:200]))
    audit("role.created", f"role:{slug}", after={"name": name}, commit=False)
    c.db.session.commit(); return _back("chere_admin.roles")


@bp.route("/roles/<int:rid>/permissions", methods=["POST"])
@require_permission("roles.manage")
def role_permissions(rid):
    c = ctx(); r = c.M.Role.query.get_or_404(rid)
    _need_confirm()
    if r.slug == "super_admin":
        abort(403, description="Super Administrator permissions are fixed")
    codes = {x for x in request.form.getlist("codes") if x in PERMISSIONS}
    old = {p.code for p in r.permissions}
    if not is_super(current_user):
        mine = effective_permissions(current_user)
        if not old <= mine or not all(can_grant(current_user, x) for x in codes - old):
            abort(403, description="You cannot edit permissions beyond your own")
    r.permissions = c.M.Permission.query.filter(c.M.Permission.code.in_(codes)).all() if codes else []
    audit("role.permissions_changed", f"role:{r.slug}", {"codes": sorted(old)}, {"codes": sorted(codes)}, commit=False)
    c.db.session.commit()
    c.notifier.notify_permission_change({"actor_id": current_user.id, "action": f"permissions du rôle {r.slug}"})
    return _back("chere_admin.roles")


@bp.route("/roles/<int:rid>/toggle", methods=["POST"])
@require_permission("roles.manage")
def role_toggle(rid):
    c = ctx(); r = c.M.Role.query.get_or_404(rid); _need_confirm()
    if r.slug == "super_admin":
        abort(403, description="Super Administrator role cannot be deactivated")
    r.is_active = not r.is_active
    audit("role.toggled", f"role:{r.slug}", after={"is_active": r.is_active}, commit=False)
    c.db.session.commit(); return _back("chere_admin.roles")


@bp.route("/modules")
@require_permission("modules.view")
def modules():
    c = ctx()
    items = []
    for name, label in sorted(c.modules.items()):
        row = c.M.ModuleSetting.query.get(name)
        items.append({"name": name, "label": label, "enabled": True if row is None else row.enabled})
    return render_template("chere_admin/modules.html", items=items)


@bp.route("/modules/<name>/toggle", methods=["POST"])
@require_permission("modules.manage")
def module_toggle(name):
    c = ctx(); _need_confirm()
    if name not in c.modules:
        abort(404)
    row = c.M.ModuleSetting.query.get(name) or c.M.ModuleSetting(name=name, enabled=True)
    row.enabled = not row.enabled
    c.db.session.add(row)
    audit("module.toggled", f"module:{name}", after={"enabled": row.enabled}, commit=False)
    c.db.session.commit(); return _back("chere_admin.modules")


@bp.route("/audit")
@require_permission("audit_logs.view")
def audit_logs():
    c = ctx(); A = c.M.AuditLog
    stmt = c.db.select(A).order_by(A.id.desc())
    f = {k: request.args.get(k, "").strip() for k in ("action", "outcome", "actor", "date_from", "date_to")}
    if f["action"]: stmt = stmt.where(A.action.ilike(f"%{f['action'][:60]}%"))
    if f["outcome"] in {"success", "failure"}: stmt = stmt.where(A.outcome == f["outcome"])
    if f["actor"].isdigit(): stmt = stmt.where(A.actor_id == int(f["actor"]))
    import datetime as dt
    for key, op in (("date_from", lambda d: A.ts >= d), ("date_to", lambda d: A.ts < d + dt.timedelta(days=1))):
        try: stmt = stmt.where(op(dt.datetime.strptime(f[key], "%Y-%m-%d")))
        except ValueError: pass
    page = c.db.paginate(stmt, page=request.args.get("page", 1, type=int), per_page=25, error_out=False)
    return render_template("chere_admin/audit.html", page=page, f=f)


@bp.route("/notifications")
@require_permission("notifications.view")
def notifications():
    c = ctx(); n = c.notifier
    page = c.db.paginate(c.db.select(c.M.NotificationLog).order_by(c.M.NotificationLog.id.desc()),
                         page=request.args.get("page", 1, type=int), per_page=25, error_out=False)
    return render_template("chere_admin/notifications.html", page=page, configured=n.configured(),
                           master=n.master_on(), min_sev=n.min_severity(), rate=n.rate_limit(),
                           events={e: n.event_on(e) for e in EVENTS}, severities=list(SEVERITY))


@bp.route("/notifications/settings", methods=["POST"])
@require_permission("notifications.manage")
def notification_settings():
    c = ctx(); n = c.notifier; _need_confirm()
    n.put("notif.enabled", "1" if request.form.get("enabled") else "0")
    sev = request.form.get("min_severity", "info")
    n.put("notif.min_severity", sev if sev in SEVERITY else "info")
    n.put("notif.rate_limit_per_hour", max(1, min(request.form.get("rate", 10, type=int), 200)))
    on = set(request.form.getlist("events"))
    for e in EVENTS:
        n.put(f"notif.evt.{e}", "1" if e in on else "0")
    audit("notifications.settings_changed", "notifications", after={"events": sorted(on), "min_severity": sev}, commit=False)
    c.db.session.commit(); flash("Notification settings saved."); return _back("chere_admin.notifications")


@bp.route("/notifications/test", methods=["POST"])
@require_permission("notifications.manage")
def notification_test():
    _need_confirm()
    row = ctx().notifier.send_test()
    audit("notifications.test_sent", "notifications", after={"status": row.status})
    flash(f"Test notification: {row.status}"); return _back("chere_admin.notifications")


@bp.route("/notifications/<int:nid>/retry", methods=["POST"])
@require_permission("notifications.manage")
def notification_retry(nid):
    row = ctx().notifier.retry(nid)
    audit("notifications.retry", f"notification:{nid}", after={"status": getattr(row, "status", "not_eligible")})
    flash("Retry attempted." if row else "Not eligible for retry."); return _back("chere_admin.notifications")
