"""Authentication routes (register, login, logout)."""

from __future__ import annotations

import os
import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from . import db
from .models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,32}$")


@auth_bp.get("/login")
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return render_template("auth/login.html", active_page="auth")


@auth_bp.post("/login")
def login_submit():
    email = (request.form.get("email") or "").strip()
    password = request.form.get("password") or ""

    user_row = db.verify_user(email, password)
    if user_row is None:
        flash("Invalid email or password.", "error")
        return redirect(url_for("auth.login_page"))

    login_user(User(user_row))
    next_url = request.args.get("next") or url_for("home")
    return redirect(next_url)


@auth_bp.get("/register")
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return render_template("auth/register.html", active_page="auth")


@auth_bp.post("/register")
def register_submit():
    email = (request.form.get("email") or "").strip().lower()
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm_password") or ""

    if not email or "@" not in email:
        flash("A valid email address is required.", "error")
        return redirect(url_for("auth.register_page"))
    if not _USERNAME_RE.match(username):
        flash("Username must be 3–32 characters (letters, numbers, underscore).", "error")
        return redirect(url_for("auth.register_page"))
    if len(password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return redirect(url_for("auth.register_page"))
    if password != confirm:
        flash("Passwords do not match.", "error")
        return redirect(url_for("auth.register_page"))

    if db.get_user_by_email(email) or db.get_user_by_username(username):
        flash("Email or username is already registered.", "error")
        return redirect(url_for("auth.register_page"))

    make_admin = db.count_users() == 0
    bootstrap_email = os.environ.get("CASTLE_ADMIN_EMAIL", "").lower()
    if bootstrap_email and email == bootstrap_email:
        make_admin = True

    user_id = db.create_user(
        email=email,
        username=username,
        password=password,
        is_admin=make_admin,
    )
    login_user(User(db.get_user_by_id(user_id)))
    flash("Account created. You are signed in.", "success")
    return redirect(url_for("home"))


@auth_bp.post("/logout")
@login_required
def logout_submit():
    logout_user()
    flash("Signed out.", "success")
    return redirect(url_for("home"))
