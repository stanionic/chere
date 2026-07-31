import json
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.blueprints.admin import admin_bp
from app.blueprints.admin.forms import LoginForm, BroadcastNotificationForm, MobileInstallSettingsForm, EventSmsBroadcastForm
from app.models import (
    User, Article, Service, Project, Partner, TeamMember,
    Statistic, Message, NewsletterSubscriber, Sector, Notification, UserNotification,
    AppInstallation, PwaConfig, Event, EventParticipant, EventSmsBroadcast, EventSmsRecipient,
)
from app.extensions import db
from app.services.sms_service import sms_service, build_whatsapp_link, format_phone_display, normalize_phone_number


def admin_required(view):
    """Décorateur simple : restreint l'accès aux comptes ayant le rôle admin."""
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_role("admin"):
            flash("Accès réservé aux administrateurs.", "danger")
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)
    return wrapped


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            from datetime import datetime
            user.last_login = datetime.utcnow()
            from app.extensions import db
            db.session.commit()
            next_page = request.args.get("next") or url_for("admin.dashboard")
            return redirect(next_page)
        flash("Email ou mot de passe incorrect.", "danger")
    return render_template("admin/login.html", form=form)


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for("admin.login"))


@admin_bp.route("/", methods=["GET", "POST"])
@login_required
def dashboard():
    stats_summary = {
        "articles": Article.query.count(),
        "services": Service.query.count(),
        "projects": Project.query.count(),
        "partners": Partner.query.count(),
        "team_members": TeamMember.query.count(),
        "sectors": Sector.query.count(),
        "unread_messages": Message.query.filter_by(is_read=False).count(),
        "newsletter_subscribers": NewsletterSubscriber.query.count(),
        "impact_stats": Statistic.query.count(),
    }
    recent_messages = Message.query.order_by(Message.created_at.desc()).limit(5).all()
    form = BroadcastNotificationForm()
    if form.validate_on_submit():
        if not current_user.has_role("admin"):
            flash("Accès réservé aux administrateurs.", "danger")
            return redirect(url_for("admin.dashboard"))
        notification = Notification(title=form.title.data.strip(), body=form.body.data.strip(), created_by=current_user)
        db.session.add(notification)
        db.session.flush()
        recipients = User.query.filter_by(is_active_account=True).all()
        for recipient in recipients:
            db.session.add(UserNotification(user=recipient, notification=notification))
        db.session.commit()
        flash("Notification envoyée à tous les utilisateurs actifs.", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/dashboard.html", stats=stats_summary, recent_messages=recent_messages, form=form)


@admin_bp.route("/notifications")
@login_required
def notifications_page():
    if not current_user.has_role("admin"):
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("admin.dashboard"))
    all_notifications = Notification.query.order_by(Notification.created_at.desc()).all()
    return render_template("admin/notifications.html", notifications=all_notifications)


@admin_bp.route("/messages")
@login_required
def messages():
    all_messages = Message.query.order_by(Message.created_at.desc()).all()
    return render_template("admin/messages.html", messages=all_messages)


@admin_bp.route("/articles")
@login_required
def articles():
    all_articles = Article.query.order_by(Article.created_at.desc()).all()
    return render_template("admin/articles.html", articles=all_articles)


@admin_bp.route("/projects")
@login_required
def projects():
    all_projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template("admin/projects.html", projects=all_projects)


@admin_bp.route("/mobile-install", methods=["GET", "POST"])
@login_required
def mobile_install():
    if not current_user.has_role("admin"):
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("admin.dashboard"))

    config = PwaConfig.query.first()
    if not config:
        config = PwaConfig(
            enabled=True,
            popup_delay=5,
            dismiss_duration_days=1,
        )
        db.session.add(config)
        db.session.commit()

    form = MobileInstallSettingsForm(obj=config)

    if form.validate_on_submit():
        config.enabled = form.enabled.data
        config.popup_delay = form.popup_delay.data
        config.dismiss_duration_days = form.dismiss_duration_days.data
        config.custom_title = form.custom_title.data
        config.custom_description = form.custom_description.data
        config.custom_button = form.custom_button.data
        db.session.commit()
        flash("Configuration de l'installation mobile mise à jour avec succès.", "success")
        return redirect(url_for("admin.mobile_install"))

    # Statistiques PWA
    total_propositions = AppInstallation.query.count()
    total_installed = AppInstallation.query.filter_by(install_completed=True).count()
    total_dismissed = AppInstallation.query.filter_by(dismissed=True).count()
    conversion_rate = 0
    if total_propositions > 0:
        conversion_rate = round((total_installed / total_propositions) * 100, 1)

    android_count = AppInstallation.query.filter_by(device_type="android").count()
    ios_count = AppInstallation.query.filter_by(device_type="ios").count()
    desktop_count = AppInstallation.query.filter_by(device_type="desktop").count()

    recent_events = (
        AppInstallation.query
        .order_by(AppInstallation.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "admin/mobile_install.html",
        form=form,
        config=config,
        stats={
            "total_propositions": total_propositions,
            "total_installed": total_installed,
            "total_dismissed": total_dismissed,
            "conversion_rate": conversion_rate,
            "by_device": {
                "android": android_count,
                "ios": ios_count,
                "desktop": desktop_count,
            },
        },
        recent_events=recent_events,
    )


def _resolve_optin_recipients(scope, specific_event_id=None):
    """Retourne la liste des participants ciblés selon le scope."""
    q = EventParticipant.query
    if scope == "optin_all":
        q = q.filter(EventParticipant.allow_future_invites.is_(True))
    elif scope == "optin_confirmed":
        q = q.filter(
            EventParticipant.allow_future_invites.is_(True),
            EventParticipant.status == "confirmed",
        )
    elif scope == "specific_event" and specific_event_id:
        q = q.filter_by(event_id=specific_event_id)
    # all_participants: pas de filtre
    participants = q.order_by(EventParticipant.registration_date.desc()).all()
    seen = set()
    unique = []
    for p in participants:
        key = normalize_phone_number(p.whatsapp or p.phone)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(p)
    return unique


def _inject_message_vars(message, participant):
    """Remplace {name}, {email}, {event} etc. dans le message."""
    if not message:
        return ""
    try:
        return message.format(
            name=(participant.full_name or "").split()[0] if participant.full_name else "",
            full_name=participant.full_name or "",
            email=participant.email or "",
            phone=participant.phone or "",
            event=participant.event.title if participant.event else "",
        )
    except (KeyError, IndexError):
        return message


# ---- Administration participants aux événements
@admin_bp.route("/event-participants")
@login_required
def event_participants():
    """Liste tous les participants aux événements (avec filtres)."""
    if not current_user.has_role("admin"):
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("admin.dashboard"))

    event_id = request.args.get("event_id", type=int)
    status_filter = request.args.get("status", "", type=str).strip()
    optin_only = request.args.get("optin", "0", type=str) == "1"
    search = request.args.get("q", "", type=str).strip()

    q = EventParticipant.query
    if event_id:
        q = q.filter_by(event_id=event_id)
    if status_filter:
        q = q.filter_by(status=status_filter)
    if optin_only:
        q = q.filter(EventParticipant.allow_future_invites.is_(True))
    if search:
        like = f"%{search}%"
        q = q.filter(
            db.or_(
                EventParticipant.full_name.ilike(like),
                EventParticipant.email.ilike(like),
                EventParticipant.phone.ilike(like),
                EventParticipant.whatsapp.ilike(like),
            )
        )

    participants = q.order_by(EventParticipant.registration_date.desc()).limit(500).all()
    events = Event.query.order_by(Event.event_date.desc().nullslast()).all()

    # Stats
    stats = {
        "total": EventParticipant.query.count(),
        "optin": EventParticipant.query.filter(EventParticipant.allow_future_invites.is_(True)).count(),
        "confirmed": EventParticipant.query.filter_by(status="confirmed").count(),
        "with_whatsapp": EventParticipant.query.filter(EventParticipant.whatsapp.isnot(None)).count(),
    }

    return render_template(
        "admin/event_participants.html",
        participants=participants,
        events=events,
        stats=stats,
        current_event_id=event_id,
        current_status=status_filter,
        optin_only=optin_only,
        search=search,
        format_phone_display=format_phone_display,
    )


# ---- Administration SMS / WhatsApp Broadcast
@admin_bp.route("/sms-broadcast", methods=["GET", "POST"])
@login_required
def sms_broadcast():
    """Création et historique des diffusions SMS/WhatsApp."""
    if not current_user.has_role("admin"):
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("admin.dashboard"))

    form = EventSmsBroadcastForm()
    events_choices = [("", "— Sélectionnez un événement —")] + [
        (e.id, f"{e.title} ({e.event_date.strftime('%d %b %Y') if e.event_date else 'N/A'})")
        for e in Event.query.order_by(Event.event_date.desc().nullslast()).all()
    ]
    form.event_id.choices = events_choices

    preview_recipients = []
    sample_message = None
    broadcast_id = None

    if request.method == "POST" and form.validate_on_submit():
        scope = form.target_scope.data
        specific_event_id = form.event_id.data if scope == "specific_event" else None
        target_event_id = None

        if scope == "specific_event" and not specific_event_id:
            flash("Veuillez sélectionner un événement cible.", "warning")
        else:
            recipients = _resolve_optin_recipients(scope, specific_event_id)
            if not recipients:
                flash("Aucun destinataire trouvé pour cette cible.", "warning")
            else:
                sample_participant = recipients[0]
                sample_message = _inject_message_vars(form.message.data, sample_participant)

                if form.submit_send.data:
                    broadcast = EventSmsBroadcast(
                        title=form.title.data,
                        message=form.message.data,
                        channel=form.channel.data,
                        target_scope=scope,
                        specific_event_id=specific_event_id,
                        event_id=target_event_id,
                        status="sending",
                        recipient_count=len(recipients),
                        created_by_id=current_user.id,
                        created_at=datetime.utcnow(),
                    )
                    db.session.add(broadcast)
                    db.session.flush()
                    broadcast_id = broadcast.id

                    sent_ok = 0
                    sent_fail = 0
                    channels_used = set()
                    if form.channel.data in ("sms", "both"):
                        channels_used.add("sms")
                    if form.channel.data in ("whatsapp", "both"):
                        channels_used.add("whatsapp")

                    for p in recipients:
                        for channel in channels_used:
                            personalized = _inject_message_vars(form.message.data, p)
                            phone_for_channel = p.whatsapp if channel == "whatsapp" else p.phone
                            normalized = normalize_phone_number(phone_for_channel or p.phone)
                            if not normalized:
                                continue
                            rcp = EventSmsRecipient(
                                broadcast_id=broadcast.id,
                                participant_id=p.id,
                                phone_number=normalized,
                                full_name=p.full_name,
                                channel=channel,
                                status="queued",
                            )
                            db.session.add(rcp)
                            db.session.flush()
                            sms_service.send_broadcast_recipient(rcp, personalized)
                            if rcp.status == "sent":
                                sent_ok += 1
                            else:
                                sent_fail += 1

                    broadcast.sent_count = sent_ok
                    broadcast.failed_count = sent_fail
                    broadcast.status = "sent" if sent_fail == 0 else ("partial" if sent_ok > 0 else "failed")
                    broadcast.sent_at = datetime.utcnow()
                    db.session.commit()
                    flash(
                        f"Diffusion envoyée : {sent_ok} envoyés / {sent_fail} échecs sur {len(recipients)} contact(s).",
                        "success" if sent_fail == 0 else "warning",
                    )
                    return redirect(url_for("admin.sms_broadcast_history", broadcast_id=broadcast.id))
                else:
                    preview_recipients = recipients[:25]

    broadcasts = EventSmsBroadcast.query.order_by(EventSmsBroadcast.created_at.desc()).limit(10).all()
    return render_template(
        "admin/sms_broadcast.html",
        form=form,
        preview_recipients=preview_recipients,
        sample_message=sample_message,
        broadcasts=broadcasts,
        format_phone_display=format_phone_display,
        build_whatsapp_link=build_whatsapp_link,
    )


@admin_bp.route("/sms-broadcast/<int:broadcast_id>")
@login_required
def sms_broadcast_history(broadcast_id):
    """Détail d'une diffusion avec ses destinataires."""
    if not current_user.has_role("admin"):
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("admin.dashboard"))

    broadcast = EventSmsBroadcast.query.get_or_404(broadcast_id)
    recipients = broadcast.recipients.order_by(EventSmsRecipient.id.asc()).all()
    return render_template(
        "admin/sms_broadcast_detail.html",
        broadcast=broadcast,
        recipients=recipients,
        format_phone_display=format_phone_display,
        build_whatsapp_link=build_whatsapp_link,
    )


# ---- Export contacts CSV / JSON (admin)
@admin_bp.route("/event-contacts/export")
@login_required
def event_contacts_export():
    """Exporte la liste des contacts opt-in au format CSV."""
    if not current_user.has_role("admin"):
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("admin.dashboard"))

    fmt = request.args.get("format", "csv", type=str).lower()
    optin_only = request.args.get("optin", "1", type=str) == "1"
    q = EventParticipant.query
    if optin_only:
        q = q.filter(EventParticipant.allow_future_invites.is_(True))
    contacts = q.order_by(EventParticipant.registration_date.desc()).all()

    if fmt == "json":
        return jsonify([
            {
                "name": c.full_name,
                "email": c.email,
                "phone": c.phone,
                "whatsapp": c.whatsapp,
                "event": c.event.title if c.event else None,
                "status": c.status,
                "optin": c.allow_future_invites,
            }
            for c in contacts
        ])

    import csv
    from io import StringIO
    from flask import Response

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Nom", "Email", "Telephone", "WhatsApp", "Evenement", "Statut", "Opt-in invitations", "Date inscription"])
    for c in contacts:
        writer.writerow([
            c.full_name or "",
            c.email or "",
            c.phone or "",
            c.whatsapp or "",
            c.event.title if c.event else "",
            c.status or "",
            "OUI" if c.allow_future_invites else "NON",
            c.registration_date.strftime("%Y-%m-%d %H:%M") if c.registration_date else "",
        ])
    output = buffer.getvalue()
    return Response(
        output,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=chere_contacts_optin.csv",
        },
    )
