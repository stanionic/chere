"""
Point d'entrée de l'application CHERE.
Community • Humanity • Empowerment • Resources • Environment
"""
import os
from app import create_app, db
from app.models import (
    User, Role, Service, Sector, PillarIcon, Project, Partner,
    Article, TeamMember, Statistic, Message, NewsletterSubscriber, MediaAsset
)

app = create_app(os.getenv("FLASK_CONFIG", "development"))


@app.shell_context_processor
def make_shell_context():
    return dict(
        db=db, User=User, Role=Role, Service=Service, Sector=Sector,
        PillarIcon=PillarIcon, Project=Project, Partner=Partner,
        Article=Article, TeamMember=TeamMember, Statistic=Statistic,
        Message=Message, NewsletterSubscriber=NewsletterSubscriber,
        MediaAsset=MediaAsset
    )


if __name__ == "__main__":
    app.run(debug=True)
