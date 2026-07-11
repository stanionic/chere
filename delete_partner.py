import os
from app import create_app, db
from app.models import Partner

app = create_app(os.getenv("FLASK_CONFIG", "development"))


def delete_partner_by_name(name):
    with app.app_context():
        partner = Partner.query.filter_by(name=name).first()
        if not partner:
            print(f"Partner not found: {name}")
            return 1
        db.session.delete(partner)
        db.session.commit()
        print(f"Deleted partner: {name}")
        return 0


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        name = sys.argv[1]
    else:
        name = "Nations Unies"
    sys.exit(delete_partner_by_name(name))
