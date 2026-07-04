from flask import Flask, render_template, request, jsonify
import pdfplumber
import os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def analyze_resume(text):

    skills = []

    if "python" in text.lower():
        skills.append("Python")

    if "machine learning" in text.lower():
        skills.append("Machine Learning")

    if "data" in text.lower():
        skills.append("Data Analysis")

    if "cloud" in text.lower():
        skills.append("Cloud Computing")

    suggestions = []

    if "Python" not in skills:
        suggestions.append("Learn Python")

    if "Machine Learning" not in skills:
        suggestions.append("Study Machine Learning basics")

    if "Cloud Computing" not in skills:
        suggestions.append("Learn AWS or Azure fundamentals")

    return skills, suggestions


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():

    file = request.files["resume"]

    if file.filename == "":
        return jsonify({"error": "No file selected"})

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    text = ""

    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""

    skills, suggestions = analyze_resume(text)

    return jsonify({
        "skills": skills,
        "suggestions": suggestions
    })


if __name__ == "__main__":
    app.run(debug=True)