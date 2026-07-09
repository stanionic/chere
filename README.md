# CHERE — Community • Humanity • Empowerment • Resources • Environment

Plateforme web internationale pour l'entreprise sociale CHERE, dédiée à l'innovation,
aux énergies renouvelables, à l'action humanitaire et au développement durable
à travers le monde.

## 🏗️ Stack technique

- **Backend** : Python, Flask, SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF, Jinja2
- **Frontend** : Bootstrap 5, Bootstrap Icons, HTML5, CSS3, JavaScript ES6, Leaflet.js
- **Base de données** : SQLite (développement) / PostgreSQL (production)
- **Architecture** : Flask Blueprints (home, about, services, innovation, renewable,
  humanitarian, projects, partners, blog, contact, admin, api)

## 🚀 Installation

```bash
# 1. Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate   # Windows : venv\Scripts\activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer les variables d'environnement
cp .env.example .env
# éditer .env si besoin (SECRET_KEY, DATABASE_URL...)

# 4. Initialiser la base de données + données de démonstration
python seed.py

# 5. Lancer l'application
python run.py
```

L'application est accessible sur **http://127.0.0.1:5000**

### Compte administrateur par défaut
- Email : `admin@chere-global.org`
- Mot de passe : `ChangeMe123!`

⚠️ **Changez ce mot de passe immédiatement en production.**

## 📁 Structure du projet

```
chere/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Configuration (dev/prod/test)
│   ├── extensions.py        # Extensions Flask centralisées
│   ├── models.py            # Modèles SQLAlchemy
│   ├── blueprints/          # Un blueprint par domaine fonctionnel
│   │   ├── home/
│   │   ├── about/
│   │   ├── services/
│   │   ├── innovation/
│   │   ├── renewable/
│   │   ├── humanitarian/
│   │   ├── projects/
│   │   ├── partners/
│   │   ├── blog/
│   │   ├── contact/
│   │   ├── admin/
│   │   └── api/
│   ├── templates/           # Templates Jinja2 (un dossier par blueprint)
│   └── static/
│       ├── css/style.css    # Design system CHERE (palette, dark/light mode)
│       ├── js/main.js       # Compteurs animés, carte, thème
│       └── img/
├── seed.py                  # Script d'initialisation des données
├── run.py                   # Point d'entrée
├── requirements.txt
└── .env.example
```

## 🎨 Design

- Palette : Royal Blue, Gold, Emerald Green, White, Light Grey, Noir élégant
- Glassmorphism léger, coins arrondis, animations fluides
- Mode sombre / clair (persistant via `localStorage`)
- Grille d'icônes (Bootstrap Icons) plutôt que de longs paragraphes
- Mobile-first, responsive (mobile / tablette / desktop)
- Carte interactive du monde (Leaflet + OpenStreetMap/CARTO) affichant les projets

## 🔐 Sécurité

- Protection CSRF (Flask-WTF)
- Authentification par session (Flask-Login) avec hachage des mots de passe (Werkzeug)
- Séparation des rôles (admin / editor)
- Validation des formulaires côté serveur

## 🗄️ Modèles de données

`User`, `Role`, `Sector`, `PillarIcon`, `Service`, `Project`, `Partner`,
`TeamMember`, `Article`, `Statistic`, `Message`, `NewsletterSubscriber`, `MediaAsset`.

## 🛠️ Prochaines étapes suggérées

- Ajouter les formulaires CRUD complets dans l'admin (actuellement lecture seule
  pour Articles/Projets, à étendre avec Flask-WTF pour la création/édition)
- Brancher un service d'envoi d'e-mails (Flask-Mail) pour les notifications
  de contact et de newsletter
- Ajouter Flask-Migrate (`flask db init/migrate/upgrade`) pour gérer les
  évolutions de schéma en production
- Optimiser les images (WebP, lazy loading) et mettre en place un cache
  (Flask-Caching) pour la production
- Déployer sur un serveur avec Gunicorn + Nginx et PostgreSQL

## 📄 Licence

Projet fourni tel quel à des fins de démonstration / point de départ pour CHERE.
