import os
from app import create_app, db
from app.models import Partner

app = create_app(os.getenv("FLASK_CONFIG", "development"))

with app.app_context():
    partners = Partner.query.order_by(Partner.id).all()
    if not partners:
        print("No partners found")
    for p in partners:
        print(p.id, p.name)
