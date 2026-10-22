"""
Formulaires de la boutique CHERE (commande + paiement MoMo).
"""
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Regexp
from app.i18n import translate


class ShopCheckoutForm(FlaskForm):
    """Formulaire de commande + paiement MoMo."""
    customer_name = StringField(
        "Nom complet",
        validators=[DataRequired(), Length(min=2, max=140)],
    )
    customer_phone = StringField(
        "Numero MoMo",
        validators=[
            DataRequired(),
            Regexp(
                r'^(\+?250)?[67]\d{8}$',
                message="Format: 250xxxxxxxxx ou 07xxxxxxxx",
            ),
        ],
    )
    quantity = IntegerField(
        "Quantite",
        validators=[DataRequired(), NumberRange(min=1, max=100)],
        default=1,
    )
    submit = SubmitField("Payer avec MoMo")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.customer_name.label.text = translate("shop.checkout.name_label")
        self.customer_name.render_kw = {"placeholder": translate("shop.checkout.name_placeholder")}
        self.customer_phone.label.text = translate("shop.checkout.momo_label")
        self.customer_phone.render_kw = {
            "placeholder": translate("shop.checkout.momo_placeholder"),
            "class": "form-control form-control-lg",
        }
        self.quantity.label.text = translate("shop.checkout.quantity_label")
        self.quantity.render_kw = {"class": "form-control"}
        self.submit.label.text = translate("shop.checkout.pay_now")

        for validator in self.customer_name.validators:
            if isinstance(validator, DataRequired):
                validator.message = translate("validation.required")
        for validator in self.customer_phone.validators:
            if isinstance(validator, DataRequired):
                validator.message = translate("validation.required")
            if isinstance(validator, Regexp):
                validator.message = translate("shop.checkout.momo_format")
