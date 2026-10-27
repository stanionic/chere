# CHERE Admin Kit (standalone)

Drop-in admin panel: RBAC, audit log, module switches, and CallMeBot WhatsApp alerts.
Built **without access to the real CHERE code**, so Phase 1 (audit of your codebase) has NOT been done.

## Plug into CHERE (adapter checklist)
1. Copy `chere_admin/` into the project; `pip install -r requirements.txt`.
2. Your `User` model needs: `id`, `username`, `email`, `status` (`active|pending|suspended|deactivated`), `created_at`,
   and must work with Flask-Login. Map your existing fields if they differ (edit `views.py`/`rbac.py`).
3. In your app factory, after `db` and `login_manager` exist:
   `init_admin(app, db, User, modules={"messaging": "Messagerie", ...})`
4. Run `flask admin-seed`, then manually attach the `super_admin` role to your first admin
   (insert into `admin_user_roles`). Existing role logic is untouched; map it onto these roles gradually.
5. Guard each CHERE module's routes with `@module_required("name")` and sensitive routes with `@require_permission("code")`.
6. Call hooks: `record_failed_login(username)` on bad passwords and `is_locked_out(username)` before checking them;
   `current_app.extensions["chere_admin"].notifier.notify_new_user({"user_id": u.id})` after registration.
7. Tables use `db.create_all()` only here. For production generate an Alembic/Flask-Migrate migration
   (`flask db migrate`), review it (additive tables only), and back up the DB first.

## Activate CallMeBot (only you can do this)
Follow the current instructions at https://www.callmebot.com/blog/free-api-whatsapp-messages/ — in short: from
+50948911268 send CallMeBot's activation message to their WhatsApp contact and wait for your personal API key.
Then set `CALLMEBOT_API_KEY`, `CALLMEBOT_PHONE=+50948911268`, `CALLMEBOT_ENABLED=true` in the server environment
and use *WhatsApp → Envoyer un message de test* in the panel. Verify the endpoint/response format against their docs;
the success check (HTTP 2xx and no "error" in body) is an assumption I could not confirm against a live account.

## Run demo / tests
`python -m pytest tests -q`   (CallMeBot is fully mocked; no real messages are sent)

## Status
Implemented: dashboard (real counts, recent events), user list (search/filter/sort/paginate), status changes,
role assignment, per-user grant/deny overrides, roles + permission matrix, role create/toggle, module enable/disable
(enforced server-side via `module_required`), audit log (append-only at ORM level, redaction, filters),
brute-force lockout + alert, CSRF, deny-by-default checks, last-super-admin protection, escalation guards,
CallMeBot service (timeouts, bounded backoff, dedupe, rate limit, severity, history, retry, test message).
Partial: charts (stat cards only); async delivery uses an in-process thread (lost on restart; use Celery/RQ for durability);
audit immutability is ORM-level (add DB triggers/privileges for real tamper resistance); i18n is French-only.
Not implemented: codebase audit, create/edit user forms, account deletion, session revocation, per-module role/user
restrictions and module health, system health page, admin profile/2FA page, audit retention job, migrations.
