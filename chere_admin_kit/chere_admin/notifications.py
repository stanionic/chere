"""CallMeBot WhatsApp notifier: async, throttled, deduplicated, bounded retries, no secret leakage."""
import os, time, logging, datetime as dt
from concurrent.futures import ThreadPoolExecutor
import requests

log = logging.getLogger("chere.notify")
CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"   # verify against callmebot.com docs
SEVERITY = {"info": 0, "warning": 1, "critical": 2}
# event -> (default enabled, default severity)
EVENTS = {
    "user.registered": (True, "info"), "account.status_changed": (True, "warning"),
    "login.bruteforce": (True, "critical"), "security.suspicious": (True, "critical"),
    "permissions.changed": (True, "warning"), "admin.created": (True, "critical"),
    "settings.security_changed": (True, "warning"), "error.critical": (True, "critical"),
    "module.failure": (True, "warning"), "account.recovery": (False, "info"),
    "approval.important": (True, "info"), "test": (True, "info"),
}
MAX_ATTEMPTS = 3


def _truthy(v):
    return str(v).strip().lower() in {"1", "true", "yes", "on"}


class Notifier:
    def __init__(self, app, c):
        self.app, self.c = app, c
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="notify")

    # ---- config (env for secrets, DB for preferences) ----
    def creds(self):
        return os.environ.get("CALLMEBOT_PHONE", "").strip(), os.environ.get("CALLMEBOT_API_KEY", "").strip()

    def configured(self):
        phone, key = self.creds()
        return _truthy(os.environ.get("CALLMEBOT_ENABLED", "false")) and bool(phone and key)

    def get(self, key, default=None):
        row = self.c.M.Setting.query.get(key)
        return row.value if row else default

    def put(self, key, value):
        row = self.c.M.Setting.query.get(key)
        if row:
            row.value = str(value)
        else:
            self.c.db.session.add(self.c.M.Setting(key=key, value=str(value)))

    def master_on(self):
        return _truthy(self.get("notif.enabled", "true"))

    def event_on(self, event):
        return _truthy(self.get(f"notif.evt.{event}", "1" if EVENTS.get(event, (True,))[0] else "0"))

    def min_severity(self):
        return self.get("notif.min_severity", "info")

    def rate_limit(self):
        return int(self.get("notif.rate_limit_per_hour", "10"))

    # ---- core API ----
    def send_whatsapp_notification(self, message, event="generic", severity="info", dedupe_key=None):
        M, db = self.c.M, self.c.db
        message = " ".join(str(message).split())[:500]
        now = dt.datetime.utcnow()
        skip = None
        if not self.master_on() or not self.event_on(event):
            skip = "disabled"
        elif SEVERITY.get(severity, 0) < SEVERITY.get(self.min_severity(), 0):
            skip = "below_min_severity"
        elif not self.configured():
            skip = "not_configured"
        elif dedupe_key and M.NotificationLog.query.filter(
                M.NotificationLog.dedupe_key == dedupe_key,
                M.NotificationLog.status.in_(["queued", "sent"]),
                M.NotificationLog.ts >= now - dt.timedelta(minutes=10)).count():
            skip = "duplicate"
        elif M.NotificationLog.query.filter(
                M.NotificationLog.status.in_(["queued", "sent"]),
                M.NotificationLog.ts >= now - dt.timedelta(hours=1)).count() >= self.rate_limit():
            skip = "rate_limited"
        row = M.NotificationLog(event=event, severity=severity, message=message, dedupe_key=dedupe_key,
                                status=f"skipped:{skip}" if skip else "queued")
        db.session.add(row)
        db.session.commit()
        if skip:
            return row
        if self.app.config.get("NOTIFY_SYNC"):
            self.deliver(row.id)
        else:                                   # never block the request on WhatsApp
            self.pool.submit(self._deliver_bg, row.id)
        return row

    def _deliver_bg(self, row_id):
        with self.app.app_context():
            try:
                self.deliver(row_id)
            except Exception as exc:            # worker must never die loudly
                log.error("notification worker error: %s", type(exc).__name__)

    def deliver(self, row_id):
        M, db = self.c.M, self.c.db
        row = M.NotificationLog.query.get(row_id)
        phone, key = self.creds()
        base = float(self.app.config.get("NOTIFY_BACKOFF_BASE", 1.0))
        for attempt in range(1, MAX_ATTEMPTS + 1):
            row.attempts = attempt
            retryable, err = False, None
            try:
                r = requests.get(CALLMEBOT_URL, timeout=(3.05, 10),
                                 params={"phone": phone, "text": row.message, "apikey": key})
                body = (r.text or "")[:300].lower()
                if 200 <= r.status_code < 300 and "error" not in body:
                    row.status, row.error = "sent", None
                    break
                err = f"HTTP {r.status_code}"
                retryable = r.status_code >= 500 or r.status_code == 429
            except requests.RequestException as exc:   # message may embed the URL+key: log class only
                err, retryable = type(exc).__name__, True
            row.status, row.error = "failed", err
            if not retryable or attempt == MAX_ATTEMPTS:
                break
            time.sleep(min(base * 2 ** (attempt - 1), 30))
        db.session.commit()
        log.info("notification %s -> %s (attempts=%s)", row.id, row.status, row.attempts)
        return row

    def retry(self, row_id):
        row = self.c.M.NotificationLog.query.get(row_id)
        if not row or row.status != "failed" or not self.configured():
            return None
        row.status, row.attempts = "queued", 0
        self.c.db.session.commit()
        return self.deliver(row.id)

    def send_test(self):
        """Real test message; only call after an explicit admin request."""
        if not self.configured():
            return self.send_whatsapp_notification("x", event="test")  # logs skipped:not_configured
        row = self.c.M.NotificationLog(event="test", severity="info", status="queued",
                                       message="CHERE ADMIN — Message de test. La connexion CallMeBot fonctionne.")
        self.c.db.session.add(row)
        self.c.db.session.commit()
        return self.deliver(row.id)

    # ---- convenience wrappers (French, no secrets, no private records) ----
    def notify_new_user(self, d):
        ts = d.get("timestamp") or dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        return self.send_whatsapp_notification(
            f"CHERE ADMIN — Nouvel utilisateur inscrit. ID: {d.get('user_id')}. Date: {ts} UTC. "
            "Consultez le tableau de bord pour les détails.", "user.registered", "info", f"reg:{d.get('user_id')}")

    def notify_security_event(self, d):
        return self.send_whatsapp_notification(
            "CHERE ALERTE — Plusieurs tentatives de connexion échouées ont été détectées. "
            "Consultez les journaux de sécurité pour examiner l'événement.",
            "login.bruteforce" if d.get("kind") == "failed_logins" else "security.suspicious",
            "critical", f"sec:{d.get('kind')}:{d.get('ref')}")

    def notify_permission_change(self, d):
        return self.send_whatsapp_notification(
            f"CHERE ADMIN — Une modification des permissions a été effectuée. Administrateur: {d.get('actor_id')}. "
            f"Action: {d.get('action')}. Consultez le journal d'audit.", "permissions.changed", "warning")

    def notify_critical_error(self, d):
        return self.send_whatsapp_notification(
            f"CHERE SYSTEM ALERT — Une erreur critique a été détectée. Référence: {d.get('error_id')}. "
            "Vérifiez les journaux du serveur.", "error.critical", "critical", f"err:{d.get('error_id')}")
