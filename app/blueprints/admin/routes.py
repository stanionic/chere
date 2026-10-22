import json
import os
import uuid
from datetime import datetime
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app.blueprints.admin import admin_bp
from app.blueprints.admin.forms import LoginForm, BroadcastNotificationForm, MobileInstallSettingsForm, EventSmsBroadcastForm, ShopProductForm
from app.models import (
    User, Article, Service, Project, Partner, TeamMember,
    Statistic, Message, NewsletterSubscriber, Sector, Notification, UserNotification,
    AppInstallation, PwaConfig, Event, EventParticipant, EventSmsBroadcast, EventSmsRecipient,
    PosOrder, BaristaOrder, Transaction, ShopProduct, ShopProductImage, ShopOrder,
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
        identifier = form.email.data.strip()
        if "@" in identifier:
            user = User.query.filter_by(email=identifier.lower()).first()
        else:
            user = User.query.filter_by(username=identifier).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            from datetime import datetime
            user.last_login = datetime.utcnow()
            from app.extensions import db
            db.session.commit()
            next_page = request.args.get("next") or url_for("admin.dashboard")
            return redirect(next_page)
        flash("Email, pseudo ou mot de passe incorrect.", "danger")
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


@admin_bp.route("/end-of-day")
@login_required
def end_of_day():
    if not current_user.has_role("admin"):
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("admin.dashboard"))

    selected_date = request.args.get("date") or datetime.utcnow().strftime("%Y-%m-%d")
    try:
        report_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
    except ValueError:
        flash("Date invalide.", "warning")
        report_date = datetime.utcnow().date()

    start = datetime.combine(report_date, datetime.min.time())
    end = start + timedelta(days=1)

    pos_orders = PosOrder.query.filter(PosOrder.created_at >= start, PosOrder.created_at < end).all()
    barista_orders = BaristaOrder.query.filter(BaristaOrder.created_at >= start, BaristaOrder.created_at < end).all()

    pos_total = sum(float(order.total_amount or 0) for order in pos_orders)
    barista_total = sum(float(order.total_amount or 0) for order in barista_orders)
    selected_day_total = pos_total + barista_total

    all_dates = set()
    for order in PosOrder.query.all():
        if order.created_at:
            all_dates.add(order.created_at.date())
    for order in BaristaOrder.query.all():
        if order.created_at:
            all_dates.add(order.created_at.date())

    daily_totals = []
    for day in sorted(all_dates, reverse=True):
        day_start = datetime.combine(day, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        pos_day_total = float(sum(
            float(order.total_amount or 0) for order in PosOrder.query.filter(PosOrder.created_at >= day_start, PosOrder.created_at < day_end).all()
        ))
        barista_day_total = float(sum(
            float(order.total_amount or 0) for order in BaristaOrder.query.filter(BaristaOrder.created_at >= day_start, BaristaOrder.created_at < day_end).all()
        ))
        daily_totals.append({
            "date": day,
            "pos_total": pos_day_total,
            "barista_total": barista_day_total,
            "total": pos_day_total + barista_day_total,
        })

    return render_template(
        "admin/end_of_day.html",
        selected_date=report_date,
        pos_orders=pos_orders,
        barista_orders=barista_orders,
        pos_total=pos_total,
        barista_total=barista_total,
        selected_day_total=selected_day_total,
        daily_totals=daily_totals,
    )


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


@admin_bp.route("/transactions")
@login_required
def transactions():
    if not current_user.has_role("admin"):
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("admin.dashboard"))

    transactions = Transaction.query.order_by(Transaction.created_at.desc()).all()
    return render_template("admin/transactions.html", transactions=transactions)


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


# ---- Boutique: gestion des produits
ALLOWED_SHOP_IMAGE_EXT = {"png", "jpg", "jpeg", "webp", "gif"}
ALLOWED_SHOP_VIDEO_EXT = {"mp4", "webm", "mov"}


def _shop_upload_dir():
    """Sous-dossier dedie aux medias de la boutique (app/static/uploads/shop)."""
    from flask import current_app
    base = os.path.join(current_app.config["UPLOAD_FOLDER"], "shop")
    os.makedirs(base, exist_ok=True)
    return base


def _unique_slug(model, name, exclude_id=None):
    from app.blueprints.shop.routes import slugify
    base = slugify(name)
    slug = base
    counter = 2
    while True:
        q = model.query.filter(model.slug == slug)
        if exclude_id:
            q = q.filter(model.id != exclude_id)
        if not q.first():
            return slug
        slug = f"{base}-{counter}"
        counter += 1


@admin_bp.route("/shop-products", methods=["GET", "POST"])
@login_required
def shop_products():
    """Liste + creation des produits de la boutique."""
    if not current_user.has_role("admin"):
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("admin.dashboard"))

    form = ShopProductForm()
    if form.validate_on_submit():
        product = ShopProduct(
            name=form.name.data.strip(),
            description=form.description.data.strip(),
            price=float(form.price.data),
            stock_quantity=form.stock_quantity.data or 0,
            is_published=bool(form.is_published.data),
            video_url=(form.video_url.data or "").strip() or None,
            external_link=(form.external_link.data or "").strip() or None,
        )
        product.slug = _unique_slug(ShopProduct, product.name)
        db.session.add(product)
        db.session.flush()

        upload_dir = _shop_upload_dir()
        # Images (max 3)
        files = [f for f in request.files.getlist("images") if f and f.filename]
        for order, file in enumerate(files[:3]):
            ext = secure_filename(file.filename).rsplit(".", 1)[-1].lower()
            if ext not in ALLOWED_SHOP_IMAGE_EXT:
                continue
            filename = f"shop_{product.id}_{uuid.uuid4().hex[:8]}.{ext}"
            file.save(os.path.join(upload_dir, filename))
            db.session.add(ShopProductImage(product_id=product.id, filename=filename, order=order))

        # Video uploadee
        video = request.files.get("video_file")
        if video and video.filename:
            ext = secure_filename(video.filename).rsplit(".", 1)[-1].lower()
            if ext in ALLOWED_SHOP_VIDEO_EXT:
                filename = f"video_{product.id}_{uuid.uuid4().hex[:8]}.{ext}"
                video.save(os.path.join(upload_dir, filename))
                product.video_file = filename

        db.session.commit()
        flash("Produit ajouté à la boutique.", "success")
        return redirect(url_for("admin.shop_products"))

    products = ShopProduct.query.order_by(ShopProduct.created_at.desc()).all()
    return render_template("admin/shop_products.html", products=products, form=form)


@admin_bp.route("/shop-products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def shop_product_edit(product_id):
    if not current_user.has_role("admin"):
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("admin.dashboard"))

    product = ShopProduct.query.get_or_404(product_id)
    form = ShopProductForm(obj=product)
    if request.method == "POST" and form.validate_on_submit():
        product.name = form.name.data.strip()
        product.description = form.description.data.strip()
        product.price = float(form.price.data)
        product.stock_quantity = form.stock_quantity.data or 0
        product.is_published = bool(form.is_published.data)
        product.video_url = (form.video_url.data or "").strip() or None
        product.external_link = (form.external_link.data or "").strip() or None

        upload_dir = _shop_upload_dir()
        # Nouvelles images ajoutees (total max 3)
        existing = len(product.images)
        files = [f for f in request.files.getlist("images") if f and f.filename]
        for offset, file in enumerate(files[: max(0, 3 - existing)]):
            ext = secure_filename(file.filename).rsplit(".", 1)[-1].lower()
            if ext not in ALLOWED_SHOP_IMAGE_EXT:
                continue
            filename = f"shop_{product.id}_{uuid.uuid4().hex[:8]}.{ext}"
            file.save(os.path.join(upload_dir, filename))
            db.session.add(ShopProductImage(product_id=product.id, filename=filename, order=existing + offset))

        video = request.files.get("video_file")
        if video and video.filename:
            ext = secure_filename(video.filename).rsplit(".", 1)[-1].lower()
            if ext in ALLOWED_SHOP_VIDEO_EXT:
                # Supprime l'ancienne video
                if product.video_file:
                    old = os.path.join(upload_dir, product.video_file)
                    if os.path.exists(old):
                        os.remove(old)
                filename = f"video_{product.id}_{uuid.uuid4().hex[:8]}.{ext}"
                video.save(os.path.join(upload_dir, filename))
                product.video_file = filename

        db.session.commit()
        flash("Produit mis à jour.", "success")
        return redirect(url_for("admin.shop_products"))

    return render_template("admin/shop_product_edit.html", product=product, form=form)


@admin_bp.route("/shop-products/<int:product_id>/image/<int:image_id>/delete", methods=["POST"])
@login_required
def shop_product_image_delete(product_id, image_id):
    if not current_user.has_role("admin"):
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("admin.dashboard"))

    image = ShopProductImage.query.filter_by(id=image_id, product_id=product_id).first_or_404()
    path = os.path.join(_shop_upload_dir(), image.filename)
    if os.path.exists(path):
        os.remove(path)
    db.session.delete(image)
    db.session.commit()
    flash("Image supprimée.", "info")
    return redirect(url_for("admin.shop_product_edit", product_id=product_id))


@admin_bp.route("/shop-products/<int:product_id>/delete", methods=["POST"])
@login_required
def shop_product_delete(product_id):
    if not current_user.has_role("admin"):
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("admin.dashboard"))

    product = ShopProduct.query.get_or_404(product_id)
    upload_dir = _shop_upload_dir()
    for image in product.images:
        path = os.path.join(upload_dir, image.filename)
        if os.path.exists(path):
            os.remove(path)
    if product.video_file:
        path = os.path.join(upload_dir, product.video_file)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(product)
    db.session.commit()
    flash("Produit supprimé.", "info")
    return redirect(url_for("admin.shop_products"))


@admin_bp.route("/shop-orders")
@login_required
def shop_orders():
    """Historique des commandes de la boutique."""
    if not current_user.has_role("admin"):
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("admin.dashboard"))

    status_filter = request.args.get("status", "", type=str).strip()
    q = ShopOrder.query
    if status_filter:
        q = q.filter_by(status=status_filter)
    orders = q.order_by(ShopOrder.created_at.desc()).limit(500).all()
    stats = {
        "total": ShopOrder.query.count(),
        "paid": ShopOrder.query.filter_by(status="paid").count(),
        "pending": ShopOrder.query.filter_by(status="pending").count(),
        "failed": ShopOrder.query.filter_by(status="failed").count(),
        "revenue": sum(float(o.total_amount or 0) for o in ShopOrder.query.filter_by(status="paid").all()),
    }
    return render_template("admin/shop_orders.html", orders=orders, stats=stats, current_status=status_filter)


@admin_bp.route("/shop-orders/<int:order_id>/status", methods=["POST"])
@login_required
def shop_order_status(order_id):
    """Met a jour le statut d'une commande (ex: delivered apres livraison)."""
    if not current_user.has_role("admin"):
        flash("Accès réservé aux administrateurs.", "danger")
        return redirect(url_for("admin.dashboard"))

    order = ShopOrder.query.get_or_404(order_id)
    new_status = request.form.get("status", "").strip()
    allowed = {"pending", "paid", "failed", "cancelled", "delivered"}
    if new_status in allowed:
        order.status = new_status
        if new_status == "paid" and not order.paid_at:
            order.paid_at = datetime.utcnow()
        db.session.commit()
        flash(f"Statut de la commande {order.reference} mis à jour : {new_status}.", "success")
    else:
        flash("Statut invalide.", "warning")
    return redirect(url_for("admin.shop_orders"))

