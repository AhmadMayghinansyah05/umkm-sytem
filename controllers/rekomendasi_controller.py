from flask import Blueprint, render_template
from services.rekomendasi_service import rekomendasi

rekomendasi_bp = Blueprint("rekomendasi", __name__)

@rekomendasi_bp.route("/rekomendasi")
def index():
    return render_template("rekomendasi/index.html", data=rekomendasi())
