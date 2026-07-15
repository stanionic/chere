"""
Formulaires pour la gestion des événements et inscriptions.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, FloatField, SelectField
from wtforms.validators import DataRequired, Email, Length, Regexp, Optional
from wtforms.widgets import TextArea


class EventRegistrationForm(FlaskForm):
    """Formulaire d'inscription aux événements."""
    full_name = StringField(
        "Nom complet",
        validators=[DataRequired(), Length(min=2, max=140)],
        render_kw={"placeholder": "Votre nom complet"}
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "votre@email.com"}
    )
    phone = StringField(
        "Numéro de téléphone",
        validators=[
            DataRequired(),
            Regexp(r'^\+?250\d{9}$|^\d{10}$', message="Format: +250XXXXXXXXX ou 07XXXXXXXX")
        ],
        render_kw={"placeholder": "+250 7xx xxx xxx"}
    )
    submit = SubmitField("S'inscrire à l'événement")


class MoMoPaymentForm(FlaskForm):
    """Formulaire de paiement MoMo."""
    phone_number = StringField(
        "Numéro MoMo",
        validators=[
            DataRequired(),
            Regexp(r'^250\d{9}$|^07\d{8}$|^06\d{8}$', message="Format: 250xxxxxxxxx ou 07xxxxxxxx")
        ],
        render_kw={
            "placeholder": "250 7xx xxx xxx",
            "class": "form-control form-control-lg"
        }
    )
    submit = SubmitField("Payer avec MoMo", render_kw={"class": "btn btn-primary btn-lg w-100"})


class EventCreationForm(FlaskForm):
    """Formulaire de création d'événement (admin)."""
    title = StringField(
        "Titre",
        validators=[DataRequired(), Length(min=5, max=180)]
    )
    description = TextAreaField(
        "Description",
        validators=[DataRequired(), Length(min=10)],
        widget=TextArea()
    )
    summary = StringField(
        "Résumé court",
        validators=[DataRequired(), Length(min=10, max=280)]
    )
    event_type = SelectField(
        "Type d'événement",
        choices=[
            ("conference", "Conférence"),
            ("workshop", "Atelier"),
            ("training", "Formation"),
            ("meetup", "Rencontre"),
            ("webinar", "Webinaire"),
            ("other", "Autre")
        ],
        validators=[DataRequired()]
    )
    is_paid = BooleanField("Événement payant")
    price = FloatField(
        "Prix (RWF)",
        validators=[Optional()],
        render_kw={"placeholder": "0.00"}
    )
    max_participants = StringField(
        "Max. participants (vide = illimité)",
        validators=[Optional()]
    )
    location = StringField(
        "Lieu",
        validators=[Optional(), Length(max=255)]
    )
    submit = SubmitField("Créer l'événement")
