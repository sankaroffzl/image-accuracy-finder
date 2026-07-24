"""Flask application for Image Accuracy Finder."""

import os
import uuid
from flask import Flask, render_template, request, jsonify, abort
from engine.orchestrator import compare_images

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "webp"}

# In-memory result store (could use a DB for production)
_results_store = {}


def _allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


def _get_ext(filename: str) -> str | None:
    parts = filename.rsplit(".", 1)
    return parts[1].lower() if len(parts) == 2 else None


@app.route("/")
def index():
    """Render the upload page."""
    return render_template("index.html")


@app.route("/compare", methods=["POST"])
def compare():
    """Accept two images, run comparison, return JSON result."""
    if "image_a" not in request.files or "image_b" not in request.files:
        return jsonify({"success": False, "error": "Both image_a and image_b are required"}), 400

    file_a = request.files["image_a"]
    file_b = request.files["image_b"]

    if file_a.filename == "" or file_b.filename == "":
        return jsonify({"success": False, "error": "Both files must have a filename"}), 400

    if not (_allowed_file(file_a.filename) and _allowed_file(file_b.filename)):
        return jsonify({
            "success": False,
            "error": "Only PNG, JPG, JPEG, and WEBP files are allowed"
        }), 400

    # Save files temporarily
    result_id = str(uuid.uuid4())
    ext_a = _get_ext(file_a.filename)
    ext_b = _get_ext(file_b.filename)
    path_a = os.path.join(app.config["UPLOAD_FOLDER"], f"{result_id}_a.{ext_a}")
    path_b = os.path.join(app.config["UPLOAD_FOLDER"], f"{result_id}_b.{ext_b}")
    file_a.save(path_a)
    file_b.save(path_b)

    try:
        result = compare_images(path_a, path_b)
        if result["success"]:
            result["id"] = result_id
            _results_store[result_id] = result
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        # Clean up uploaded files
        try:
            if os.path.exists(path_a):
                os.remove(path_a)
            if os.path.exists(path_b):
                os.remove(path_b)
        except OSError:
            pass


@app.route("/results/<result_id>")
def results(result_id):
    """Render the results page for a given comparison ID."""
    result = _results_store.get(result_id)
    if result is None:
        abort(404)
    return render_template("results.html", result=result)


@app.errorhandler(404)
def not_found(e):
    return render_template("index.html", error="Results not found"), 404


@app.errorhandler(413)
def too_large(e):
    return jsonify({"success": False, "error": "File too large. Maximum is 16MB."}), 413


if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
