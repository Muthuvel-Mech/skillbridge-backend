from flask import Flask, request, jsonify
import os
import vertexai
from vertexai.generative_models import GenerativeModel
from fpdf import FPDF

app = Flask(__name__)

# Get environment variables
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_LOCATION")
MODEL_ID = os.getenv("MODEL_ID", "gemini-1.5-flash")

# Init Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel(MODEL_ID)

@app.route("/api/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    user_input = data.get("input", "")
    response = model.generate_content(user_input)
    return jsonify({"recommendations": response.text})

@app.route("/api/save", methods=["POST"])
def save():
    data = request.get_json()
    content = data.get("content", "")
    # TODO: Firestore integration
    return jsonify({"status": "saved", "content": content})

@app.route("/api/history", methods=["GET"])
def history():
    # TODO: Firestore integration
    return jsonify([])

@app.route("/api/export_pdf", methods=["POST"])
def export_pdf():
    data = request.get_json()
    content = data.get("content", "")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, content)
    pdf_output = "/tmp/report.pdf"
    pdf.output(pdf_output)

    return jsonify({"status": "exported"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
