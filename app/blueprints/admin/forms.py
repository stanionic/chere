from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Mot de passe", validators=[DataRequired()])
    remember = BooleanField("Se souvenir de moi")


class BroadcastNotificationForm(FlaskForm):
    title = StringField("Titre", validators=[DataRequired()])
    body = TextAreaField("Message", validators=[DataRequired()])
    submit = SubmitField("Envoyer aux utilisateurs")
