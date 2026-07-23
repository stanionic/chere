"""
Routes du module PWA (manifest dynamique, événements d'installation, stats).
"""
import json
from datetime import datetime
from flask import jsonify, request, current_app
from app.blueprints.pwa import pwa_bp
from app.models import AppInstallation, PwaConfig
from app.extensions import db


@pwa_bp.route("/api/v1/pwa/install-event", methods=["POST"])
def record_install_event():
    """
    Enregistre un événement d'installation PWA (proposition, installation, refus).
    Reçoit un payload JSON depuis le JavaScript install.js.
    """
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    if not data or "action" not in data:
        return jsonify({"error": "Missing 'action' field"}), 400

    action = data.get("action")
    record = AppInstallation(
        device_type=data.get("device_type", "unknown"),
        browser=data.get("browser", "unknown"),
        os=data.get("os", ""),
        language=data.get("language", ""),
        action=action,
        install_requested=(action == "requested"),
        install_completed=(action == "completed" or action == "installed"),
        dismissed=(action == "dismissed"),
    )

    # Si utilisateur connecté, lier l'enregistrement
    from flask_login import current_user
    if current_user.is_authenticated:
        record.user_id = current_user.id

    db.session.add(record)
    db.session.commit()

    return jsonify({"status": "ok", "record_id": record.id}), 201


@pwa_bp.route("/api/v1/pwa/stats")
def pwa_stats():
    """
    Retourne les statistiques d'installation pour l'administration.
    """
    total_propositions = AppInstallation.query.count()
    total_installed = AppInstallation.query.filter_by(install_completed=True).count()
    total_dismissed = AppInstallation.query.filter_by(dismissed=True).count()

    # Taux de conversion (si des propositions ont été faites)
    conversion_rate = 0
    if total_propositions > 0:
        conversion_rate = round((total_installed / total_propositions) * 100, 1)

    # Répartition par appareil
    android_count = AppInstallation.query.filter_by(device_type="android").count()
    ios_count = AppInstallation.query.filter_by(device_type="ios").count()
    desktop_count = AppInstallation.query.filter_by(device_type="desktop").count()

    # Derniers événements
    recent = (
        AppInstallation.query
        .order_by(AppInstallation.created_at.desc())
        .limit(10)
        .all()
    )

    return jsonify({
        "total_propositions": total_propositions,
        "total_installed": total_installed,
        "total_dismissed": total_dismissed,
        "conversion_rate": conversion_rate,
        "by_device": {
            "android": android_count,
            "ios": ios_count,
            "desktop": desktop_count,
        },
        "recent": [
            {
                "id": r.id,
                "device_type": r.device_type,
                "action": r.action,
                "browser": r.browser,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in recent
        ],
    })


@pwa_bp.route("/api/v1/pwa/config", methods=["GET"])
def get_pwa_config():
    """
    Renvoie la configuration PWA actuelle pour le JavaScript côté client.
    """
    config = PwaConfig.query.first()
    if not config:
        # Configuration par défaut si aucune n'existe
        config = PwaConfig(
            enabled=True,
            popup_delay=5,
            dismiss_duration_days=1,
            custom_title=None,
            custom_description=None,
            custom_button=None,
        )
        db.session.add(config)
        db.session.commit()

    return jsonify({
        "enabled": config.enabled,
        "popup_delay": config.popup_delay,
        "dismiss_duration_days": config.dismiss_duration_days,
        "custom_title": config.custom_title,
        "custom_description": config.custom_description,
        "custom_button": config.custom_button,
    })
