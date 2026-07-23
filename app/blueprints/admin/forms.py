from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, Optional, NumberRange


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
