from flask import Flask, render_template, jsonify, g
from database.db import get_db
from database.models import Stock

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")


@app.route("/data", methods=["GET", "POST"])
def data():
    db = g.get('db', None)
    if db is None:
        db = next(get_db())
        g.db = db

    data = db.query(Stock).all()
    return jsonify([{'id': item.title, 'value': item.last} for item in data])


@app.teardown_appcontext
def shutdown_session(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


if __name__ == "__main__":
    app.run()
