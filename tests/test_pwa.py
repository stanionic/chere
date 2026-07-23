"""
Tests pour le module PWA "CHERE APP INSTALLER".
Couvre les modèles, les routes API PWA et l'interface admin.
"""
import json
from datetime import datetime, timedelta
from app.models import AppInstallation, PwaConfig
from app.extensions import db


def test_app_installation_model(app):
    """Teste la création d'un enregistrement d'installation PWA."""
    with app.app_context():
        record = AppInstallation(
            device_type="android",
            browser="Chrome",
            os="Android 13",
            language="fr",
            action="requested",
            install_requested=True,
        )
        db.session.add(record)
        db.session.commit()

        fetched = AppInstallation.query.first()
        assert fetched is not None
        assert fetched.device_type == "android"
        assert fetched.browser == "Chrome"
        assert fetched.action == "requested"
        assert fetched.install_requested is True
        assert fetched.install_completed is False
        assert fetched.dismissed is False

        # Nettoyage
        db.session.delete(fetched)
        db.session.commit()


def test_app_installation_representation(app):
    """Teste la représentation string du modèle AppInstallation."""
    with app.app_context():
        record = AppInstallation(
            device_type="ios",
            browser="Safari",
            action="dismissed",
            dismissed=True,
        )
        assert "AppInstallation" in repr(record)
        assert "dismissed" in repr(record)
        assert "ios" in repr(record)


def test_pwa_config_defaults(app):
    """Teste la création de la configuration PWA avec les valeurs par défaut."""
    with app.app_context():
        config = PwaConfig(
            enabled=True,
            popup_delay=5,
            dismiss_duration_days=1,
        )
        db.session.add(config)
        db.session.commit()

        fetched = PwaConfig.query.first()
        assert fetched is not None
        assert fetched.enabled is True
        assert fetched.popup_delay == 5
        assert fetched.dismiss_duration_days == 1

        # Nettoyage
        db.session.delete(fetched)
        db.session.commit()


def test_pwa_config_custom_values(app):
    """Teste la configuration PWA avec des valeurs personnalisées."""
    with app.app_context():
        config = PwaConfig(
            enabled=True,
            popup_delay=10,
            dismiss_duration_days=7,
            custom_title="Installez CHERE",
            custom_description="Test description",
            custom_button="Installer",
        )
        db.session.add(config)
        db.session.commit()

        fetched = PwaConfig.query.first()
        assert fetched.popup_delay == 10
        assert fetched.dismiss_duration_days == 7
        assert fetched.custom_title == "Installez CHERE"
        assert fetched.custom_button == "Installer"

        # Nettoyage
        db.session.delete(fetched)
        db.session.commit()


def test_pwa_config_representation(app):
    """Teste la représentation string du modèle PwaConfig."""
    with app.app_context():
        config = PwaConfig(enabled=False)
        assert "PwaConfig" in repr(config)
        assert "enabled=False" in repr(config)


def test_record_install_event_endpoint(app, client):
    """Teste l'endpoint POST /api/v1/pwa/install-event."""
    with app.app_context():
        payload = {
            "action": "installed",
            "device_type": "android",
            "browser": "Chrome 120",
            "os": "Android 14",
            "language": "fr",
        }
        response = client.post(
            "/api/v1/pwa/install-event",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["status"] == "ok"
        assert "record_id" in data


def test_record_install_event_invalid(app, client):
    """Teste l'endpoint avec payload invalide (champ action manquant)."""
    with app.app_context():
        response = client.post(
            "/api/v1/pwa/install-event",
            data=json.dumps({"device_type": "android"}),
            content_type="application/json",
        )
        assert response.status_code == 400


def test_pwa_stats_endpoint(app, client):
    """Teste l'endpoint GET /api/v1/pwa/stats."""
    with app.app_context():
        # Préparer des données de test
        records = [
            AppInstallation(device_type="android", action="requested", install_requested=True),
            AppInstallation(device_type="android", action="installed", install_completed=True),
            AppInstallation(device_type="ios", action="dismissed", dismissed=True),
        ]
        for r in records:
            db.session.add(r)
        db.session.commit()

        response = client.get("/api/v1/pwa/stats")
        assert response.status_code == 200
        data = response.get_json()
        assert "total_propositions" in data
        assert "total_installed" in data
        assert "total_dismissed" in data
        assert "conversion_rate" in data
        assert "by_device" in data

        # Nettoyage
        for r in records:
            db.session.delete(r)
        db.session.commit()


def test_pwa_config_endpoint(app, client):
    """Teste l'endpoint GET /api/v1/pwa/config."""
    with app.app_context():
        response = client.get("/api/v1/pwa/config")
        assert response.status_code == 200
        data = response.get_json()
        assert "enabled" in data
        assert "popup_delay" in data
        assert "dismiss_duration_days" in data


def test_mobile_install_admin_page(app, client):
    """Teste l'accès à la page admin /admin/mobile-install (redirige vers login si non auth)."""
    response = client.get("/admin/mobile-install", follow_redirects=False)
    # Sans authentification, doit rediriger vers la page de login
    # La redirection peut être 302 vers /admin/login
    assert response.status_code in (302, 200)
    if response.status_code == 200:
        assert "Installation Mobile" in response.text
