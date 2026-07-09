from flask import render_template, redirect, url_for, flash
from app.blueprints.contact import contact_bp
from app.blueprints.contact.forms import ContactForm, NewsletterForm
from app.models import Message, NewsletterSubscriber
from app.extensions import db


@contact_bp.route("/", methods=["GET", "POST"])
def index():
    form = ContactForm()
    if form.validate_on_submit():
        message = Message(
            full_name=form.full_name.data,
            email=form.email.data,
            subject=form.subject.data,
            body=form.body.data,
        )
        db.session.add(message)
        db.session.commit()
        flash("Merci ! Votre message a bien été envoyé à l'équipe CHERE.", "success")
        return redirect(url_for("contact.index"))
    return render_template("contact/index.html", form=form)


@contact_bp.route("/newsletter", methods=["POST"])
def newsletter():
    form = NewsletterForm()
    if form.validate_on_submit():
        existing = NewsletterSubscriber.query.filter_by(email=form.email.data).first()
        if not existing:
            db.session.add(NewsletterSubscriber(email=form.email.data))
            db.session.commit()
        flash("Merci pour votre inscription à la newsletter CHERE !", "success")
    else:
        flash("Adresse email invalide.", "danger")
    return redirect(url_for("home.index"))
