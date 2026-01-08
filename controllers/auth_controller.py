from flask import Blueprint, render_template, request, redirect, session
from models.user import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = User.authenticate(
            request.form["email"],
            request.form["password"]
        )
        if user:
            session["user_id"] = user["id"]
            return redirect("/dashboard")
    return render_template("auth/login.html")
