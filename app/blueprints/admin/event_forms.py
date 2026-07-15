"""
Admin forms pour la gestion des événements.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, FloatField, SelectField, IntegerField, DateTimeField
from wtforms.validators import DataRequired, Email, Length, Regexp, Optional, NumberRange
from wtforms.widgets import TextArea


class AdminEventForm(FlaskForm):
    """Formulaire de création/édition d'événement (admin)."""
    title = StringField(
        "Titre",
        validators=[DataRequired(), Length(min=5, max=180)]
    )
    slug = StringField(
        "URL slug",
        validators=[DataRequired(), Length(min=5, max=200)]
    )
    summary = TextAreaField(
        "Résumé (280 caractères max)",
        validators=[DataRequired(), Length(min=10, max=280)]
    )
    description = TextAreaField(
        "Description complète",
        validators=[DataRequired(), Length(min=20)],
        widget=TextArea()
    )
    event_type = SelectField(
        "Type d'événement",
        choices=[
            ("barista", "Barista"),
            ("workshop", "Atelier"),
            ("conference", "Conférence"),
            ("training", "Formation"),
            ("meetup", "Rencontre"),
            ("webinar", "Webinaire"),
            ("other", "Autre")
        ],
        validators=[DataRequired()]
    )
    
    # Pricing
    is_paid = BooleanField("Événement payant")
    price = FloatField(
        "Prix (RWF)",
        validators=[Optional(), NumberRange(min=0)],
        render_kw={"placeholder": "0.00"}
    )
    
    # Event Details
    location = StringField(
        "Lieu",
        validators=[Optional(), Length(max=255)]
    )
    event_date = DateTimeField(
        "Date et heure de début",
        format='%Y-%m-%d %H:%M',
        validators=[Optional()]
    )
    event_end_date = DateTimeField(
        "Date et heure de fin",
        format='%Y-%m-%d %H:%M',
        validators=[Optional()]
    )
    registration_deadline = DateTimeField(
        "Limite d'inscription",
        format='%Y-%m-%d %H:%M',
        validators=[Optional()]
    )
    max_participants = IntegerField(
        "Nombre max de participants (vide = illimité)",
        validators=[Optional(), NumberRange(min=1)]
    )
    
    # Publishing
    is_published = BooleanField("Publié")
    
    cover_image = StringField(
        "URL de l'image de couverture",
        validators=[Optional()]
    )
    
    submit = SubmitField("Enregistrer l'événement")


class AdminParticipantForm(FlaskForm):
    """Formulaire de gestion d'un participant."""
    full_name = StringField("Nom complet", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Téléphone", validators=[DataRequired()])
    status = SelectField(
        "Statut",
        choices=[
            ("pending", "En attente"),
            ("confirmed", "Confirmé"),
            ("cancelled", "Annulé"),
            ("no_show", "Absent")
        ]
    )
    notes = TextAreaField("Notes", validators=[Optional()], widget=TextArea())
    submit = SubmitField("Mettre à jour")
