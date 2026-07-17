from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, EmailField
from wtforms.validators import DataRequired, Email, Length
from app.i18n import translate


class ContactForm(FlaskForm):
    full_name = StringField("Nom complet", validators=[DataRequired(), Length(max=140)])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    subject = StringField("Sujet", validators=[Length(max=200)])
    body = TextAreaField("Message", validators=[DataRequired(), Length(max=3000)])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.full_name.label.text = translate("contact.form.full_name")
        self.full_name.render_kw = {"placeholder": translate("contact.form.full_name_placeholder")}
        self.email.label.text = translate("contact.form.email")
        self.email.render_kw = {"placeholder": translate("contact.form.email_placeholder")}
        self.subject.label.text = translate("contact.form.subject")
        self.subject.render_kw = {"placeholder": translate("contact.form.subject_placeholder")}
        self.body.label.text = translate("contact.form.body")
        self.body.render_kw = {"placeholder": translate("contact.form.body_placeholder")}

        for field in (self.full_name, self.email, self.body):
            for validator in field.validators:
                if isinstance(validator, DataRequired):
                    validator.message = translate("validation.required")

        for validator in self.email.validators:
            if isinstance(validator, Email):
                validator.message = translate("validation.invalid_email")


class NewsletterForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email.label.text = translate("contact.form.email")
        self.email.render_kw = {"placeholder": translate("contact.form.email_placeholder")}

        for validator in self.email.validators:
            if isinstance(validator, DataRequired):
                validator.message = translate("validation.required")
            if isinstance(validator, Email):
                validator.message = translate("validation.invalid_email")
