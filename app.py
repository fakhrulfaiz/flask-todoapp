from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# --- Database config ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'todo.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# --- Model ---
class Todo(db.Model):
    __tablename__ = "todos"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "done": self.done}


# Create tables on startup
with app.app_context():
    db.create_all()


# ===========================================================
# HTML Page Routes (Jinja2)
# ===========================================================

@app.route("/", methods=["GET"])
def index():
    todos = Todo.query.order_by(Todo.id).all()
    return render_template("index.html", todos=todos)


@app.route("/ui/todos", methods=["POST"])
def ui_create_todo():
    title = request.form.get("title", "").strip()
    if title:
        todo = Todo(title=title)
        db.session.add(todo)
        db.session.commit()
    return redirect(url_for("index"))


@app.route("/ui/todos/<int:todo_id>/toggle", methods=["POST"])
def ui_toggle_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if todo:
        todo.done = not todo.done
        db.session.commit()
    return redirect(url_for("index"))


@app.route("/ui/todos/<int:todo_id>/delete", methods=["POST"])
def ui_delete_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if todo:
        db.session.delete(todo)
        db.session.commit()
    return redirect(url_for("index"))


# ===========================================================
# REST API Routes (JSON)
# ===========================================================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/todos", methods=["GET"])
def get_todos():
    todos = Todo.query.order_by(Todo.id).all()
    return jsonify([t.to_dict() for t in todos]), 200


@app.route("/todos/<int:todo_id>", methods=["GET"])
def get_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if not todo:
        return jsonify({"error": "Todo not found"}), 404
    return jsonify(todo.to_dict()), 200


@app.route("/todos", methods=["POST"])
def create_todo():
    data = request.get_json()
    if not data or not data.get("title"):
        return jsonify({"error": "Title is required"}), 400

    todo = Todo(title=data["title"])
    db.session.add(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 201


@app.route("/todos/<int:todo_id>", methods=["PUT"])
def update_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if not todo:
        return jsonify({"error": "Todo not found"}), 404

    data = request.get_json()
    if "title" in data:
        todo.title = data["title"]
    if "done" in data:
        todo.done = data["done"]

    db.session.commit()
    return jsonify(todo.to_dict()), 200


@app.route("/todos/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if not todo:
        return jsonify({"error": "Todo not found"}), 404
    db.session.delete(todo)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
