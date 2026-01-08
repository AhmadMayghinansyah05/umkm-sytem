from flask import Blueprint, render_template, request
from services.prediksi_service import prediksi

prediksi_bp = Blueprint("prediksi", __name__)

@prediksi_bp.route("/prediksi", methods=["GET","POST"])
def index():
    hasil = None
    if request.method == "POST":
        hasil = prediksi(int(request.form["hari"]))
    return render_template("prediksi/index.html", hasil=hasil)
