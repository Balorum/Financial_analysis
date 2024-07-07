from flask import Flask, render_template, jsonify, g
from database.db import get_db
from database.models import Stock
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from parsing import currency_parser

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")


@app.route("/stock/<int:stock_id>", methods=["GET", "POST"])
def stock_detail(stock_id):
    db = g.get('db', None)
    if db is None:
        db = next(get_db())
        g.db = db

    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    return render_template("stock.html", stock=stock)


@app.route("/data", methods=["GET", "POST"])
def data():
    db = g.get('db', None)
    if db is None:
        db = next(get_db())
        g.db = db

    data = db.query(Stock).all()
    return jsonify(
        [{"id": item.id,
          'title': item.title,
          'last': item.last,
          'high': item.high,
          'low': item.low,
          "volume": item.volume,
          "change": item.change,
          "change_pct": item.change_pct,
          "growth": item.growth} for item in data])


@app.teardown_appcontext
def shutdown_session(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


scheduler = BackgroundScheduler()
scheduler.add_job(func=currency_parser.update_companies, trigger="interval", seconds=7)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    app.run()
