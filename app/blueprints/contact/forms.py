from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, EmailField
from wtforms.validators import DataRequired, Email, Length


class ContactForm(FlaskForm):
    full_name = StringField("Nom complet", validators=[DataRequired(), Length(max=140)])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    subject = StringField("Sujet", validators=[Length(max=200)])
    body = TextAreaField("Message", validators=[DataRequired(), Length(max=3000)])


class NewsletterForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
