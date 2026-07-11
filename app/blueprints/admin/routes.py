from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.blueprints.admin import admin_bp
from app.blueprints.admin.forms import LoginForm, BroadcastNotificationForm
from app.models import (
    User, Article, Service, Project, Partner, TeamMember,
    Statistic, Message, NewsletterSubscriber, Sector, Notification, UserNotification
)
from app.extensions import db


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
