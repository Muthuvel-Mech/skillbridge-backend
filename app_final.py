import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from fpdf import FPDF
from google.cloud import aiplatform, firestore
from dotenv import load_dotenv
import tempfile

# ----------------------
# Load environment
# ----------------------
load_dotenv()
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project-id")
LOCATION = os.getenv("GCP_LOCATION", "us-central1")
MODEL_ID = os.getenv("MODEL_ID", "gemini-1.5-flash")
FIRESTORE_ENABLED = os.getenv("FIRESTORE_ENABLED", "true").lower() == "true"

# ----------------------
# Initialize Flask
# ----------------------
app = Flask(__name__)
CORS(app)

# ----------------------
# Initialize Vertex AI
# ----------------------
aiplatform.init(project=PROJECT_ID, location=LOCATION)
model = aiplatform.GenerativeModel(MODEL_ID)

# ----------------------
# Firestore (optional)
# ----------------------
db = None
if FIRESTORE_ENABLED:
    try:
        db = firestore.Client()
    except Exception as e:
        print("⚠️ Firestore not available:", e)

# ----------------------
# API: Career Recommendation
# ----------------------
@app.route("/api/recommend", methods=["POST"])
def recommend():
    data = request.json
    user_input = data.get("input", "")
    if not user_input:
        return jsonify({"error": "Missing input"}), 400

    prompt = f"""
    You are SkillBridge AI, a career advisor. 
    Suggest exactly 3 career paths for: {user_input}.
    For each path, list 3 required skills.
    Answer clearly in bullet points.
    """

    try:
        response = model.generate_content(prompt)

        # ✅ Fix: sometimes .text can be None
        text = response.text if response and hasattr(response, "text") else "No recommendations available."
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"recommendations": text})

# ----------------------
# API: Save Data
# ----------------------
@app.route("/api/save", methods=["POST"])
def save():
    if not db:
        return jsonify({"error": "Firestore disabled"}), 503

    data = request.json
    try:
        doc_ref = db.collection("skillbridge_history").add(data)
        return jsonify({"status": "saved", "doc_id": doc_ref[1].id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------
# API: Get History
# ----------------------
@app.route("/api/history", methods=["GET"])
def history():
    if not db:
        return jsonify({"error": "Firestore disabled"}), 503

    try:
        docs = db.collection("skillbridge_history").stream()
        history = [doc.to_dict() for doc in docs]
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------
# API: Export PDF
# ----------------------
@app.route("/api/export_pdf", methods=["POST"])
def export_pdf():
    data = request.json
    content = data.get("content", "No content provided")

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, content)

        tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(tmpfile.name)
        return send_file(tmpfile.name, as_attachment=True, download_name="SkillBridge_Report.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------
# Health check
# ----------------------
@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "SkillBridge AI Backend running"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
