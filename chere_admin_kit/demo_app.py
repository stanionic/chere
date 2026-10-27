"""Minimal stand-in for CHERE so the admin kit can run and be tested standalone.
In the real app you only copy the `init_admin(...)` call, not this file."""
import os, datetime as dt
from flask import Flask, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from chere_admin import init_admin, module_required, record_failed_login
from chere_admin.audit import is_locked_out


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.environ.get("SECRET_KEY", os.urandom(16).hex()),
                      SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///demo.db"),
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
    app.config.update(config or {})
    db = SQLAlchemy(app)

    class User(db.Model, UserMixin):
        __tablename__ = "user"
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True)
        password_hash = db.Column(db.String(255))
        status = db.Column(db.String(20), default="active", nullable=False)
        created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

    lm = LoginManager(app)
    lm.user_loader(lambda i: db.session.get(User, int(i)))
    c = init_admin(app, db, User, modules={"messaging": "Messagerie", "reports": "Rapports"})

    @app.post("/login")
    def login():
        name, pw = request.form.get("username", ""), request.form.get("password", "")
        if is_locked_out(name):
            return jsonify(error="locked"), 429
        u = User.query.filter_by(username=name).first()
        if u and u.status == "active" and check_password_hash(u.password_hash, pw):
            login_user(u); return jsonify(ok=True)
        record_failed_login(name)
        return jsonify(error="invalid"), 401

    @app.post("/logout")
    def logout():
        logout_user(); return jsonify(ok=True)

    @app.get("/messaging")
    @module_required("messaging")
    def messaging():
        return jsonify(ok=True)

    with app.app_context():
        db.create_all()
    app.User, app.db, app.chere = User, db, c
    app.hash = generate_password_hash
    return app
