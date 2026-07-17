"""
Point d'entrée de l'application CHERE.
Community • Humanity • Empowerment • Resources • Environment
"""
import os
from datetime import datetime
from app import create_app, db
from app.models import (
    User, Role, Service, Sector, PillarIcon, Project, Partner,
    Article, TeamMember, Statistic, Message, NewsletterSubscriber, MediaAsset,
    Event, EventParticipant, Transaction, BaristaMenu, BaristaOrder, BaristaOrderItem
)

app = create_app(os.getenv("FLASK_CONFIG", "development"))


@app.shell_context_processor
def make_shell_context():
    return dict(
        db=db, User=User, Role=Role, Service=Service, Sector=Sector,
        PillarIcon=PillarIcon, Project=Project, Partner=Partner,
        Article=Article, TeamMember=TeamMember, Statistic=Statistic,
        Message=Message, NewsletterSubscriber=NewsletterSubscriber,
        MediaAsset=MediaAsset, Event=Event, EventParticipant=EventParticipant,
        Transaction=Transaction, BaristaMenu=BaristaMenu,
        BaristaOrder=BaristaOrder, BaristaOrderItem=BaristaOrderItem
    )


def bootstrap_dev_data():
    db.create_all()

    if not Event.query.filter_by(slug="cooking-class").first():
        db.session.add(Event(
            title="COOKING CLASS",
            slug="cooking-class",
            description="Join our hands-on cooking class and discover the art of preparing delicious meals.",
            summary="Hands-on cooking class with professional chefs.",
            event_type="workshop",
            is_paid=True,
            price=1000.0,
            currency="RWF",
            location="CHERE Hub, Kigali",
            event_date=datetime(2026, 8, 15, 10, 0),
            is_published=True,
        ))

    barista_event = Event.query.filter_by(slug="barista-coffee-experience").first()
    if not barista_event:
        db.session.add(Event(
            title="Barista Coffee Experience",
            slug="barista-coffee-experience",
            description="Order from our full Barista menu, enjoy live coffee service, and pay with MoMo as part of the CHERE experience.",
            summary="Full barista menu with MoMo ordering.",
            event_type="barista",
            is_paid=True,
            price=500.0,
            currency="RWF",
            location="CHERE Hub, Kigali",
            event_date=datetime(2026, 8, 20, 9, 0),
            is_published=True,
        ))
    else:
        barista_event.is_paid = True
        barista_event.price = 500.0

    if not BaristaMenu.query.first():
        menu_items = [
            ("Espresso", "espresso", "Double shot espresso rich and bold", 800, "☕", 1),
            ("Americano", "espresso", "Espresso with hot water", 900, "☕", 2),
            ("Cappuccino", "espresso", "Espresso with steamed milk and foam", 1200, "☕", 3),
            ("Latte", "espresso", "Espresso with lots of steamed milk", 1300, "☕", 4),
            ("Mocha", "espresso", "Espresso with chocolate and steamed milk", 1500, "☕", 5),
            ("Macchiato", "espresso", "Espresso with a spot of foam", 1000, "☕", 6),
            ("Green Tea", "tea", "Fresh green tea", 1000, "🍵", 7),
            ("Black Tea", "tea", "Classic black tea", 1000, "🍵", 8),
            ("Croissant", "pastry", "Buttery, flaky pastry", 800, "🥐", 9),
            ("Pain au Chocolat", "pastry", "Chocolate-filled pastry", 1000, "🥐", 10),
        ]
        for name, category, description, price, icon, order in menu_items:
            db.session.add(BaristaMenu(
                name=name,
                category=category,
                description=description,
                price=price,
                icon=icon,
                order=order,
                is_available=True,
            ))

    db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        bootstrap_dev_data()
    app.run(debug=True)
