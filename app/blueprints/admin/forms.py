from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, IntegerField, SelectMultipleField
from wtforms.validators import DataRequired, Email, Optional, NumberRange, Length


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Mot de passe", validators=[DataRequired()])
    remember = BooleanField("Se souvenir de moi")


class BroadcastNotificationForm(FlaskForm):
    title = StringField("Titre", validators=[DataRequired()])
    body = TextAreaField("Message", validators=[DataRequired()])
    submit = SubmitField("Envoyer aux utilisateurs")


class MobileInstallSettingsForm(FlaskForm):
    enabled = BooleanField("Activer le popup d'installation")
    popup_delay = SelectField(
        "Temps avant affichage",
        choices=[
            ("3", "3 secondes"),
            ("5", "5 secondes"),
            ("10", "10 secondes"),
            ("15", "15 secondes"),
            ("30", "30 secondes"),
        ],
        coerce=int,
        default=5,
    )
    dismiss_duration_days = IntegerField(
        "Jours avant réaffichage après refus",
        validators=[Optional(), NumberRange(min=1, max=90)],
        default=1,
    )
    custom_title = StringField(
        "Titre personnalisé (optionnel)",
        validators=[Optional()],
    )
    custom_description = StringField(
        "Description personnalisée (optionnel)",
        validators=[Optional()],
    )
    custom_button = StringField(
        "Texte du bouton personnalisé (optionnel)",
        validators=[Optional()],
    )
    submit = SubmitField("Enregistrer la configuration")


class EventSmsBroadcastForm(FlaskForm):
    """Formulaire pour créer une diffusion SMS/WhatsApp."""
    title = StringField(
        "Titre de la campagne",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"placeholder": "Ex: Invitation Barista Experience Mars"},
    )
    message = TextAreaField(
        "Message",
        validators=[DataRequired(), Length(max=1600)],
        render_kw={
            "placeholder": (
                "Bonjour {name}, CHERE vous invite à notre prochain événement !\n"
                "📅 Date: ...\n"
                "📍 Lieu: ...\n"
                "👉 Inscrivez-vous ici: https://..."
            ),
            "rows": 7,
        },
    )
    channel = SelectField(
        "Canal d'envoi",
        choices=[
            ("whatsapp", "WhatsApp (liens wa.me)"),
            ("sms", "SMS"),
            ("both", "SMS + WhatsApp"),
        ],
        default="whatsapp",
        validators=[DataRequired()],
    )
    target_scope = SelectField(
        "Cible",
        choices=[
            ("optin_all", "Tous les contacts consentants (opt-in)"),
            ("optin_confirmed", "Tous les inscriptions confirmées + opt-in"),
            ("specific_event", "Participants d'un événement précis"),
            ("all_participants", "Tous les participants sans filtre"),
        ],
        default="optin_all",
        validators=[DataRequired()],
    )
    event_id = SelectField(
        "Événement cible (si Cible = spécifique)",
        choices=[("", "— Sélectionnez un événement —")],
        coerce=int,
        default="",
        validators=[Optional()],
    )
    submit_preview = SubmitField("Prévisualiser & Sélectionner")
    submit_send = SubmitField("🚀 Envoyer immédiatement")
