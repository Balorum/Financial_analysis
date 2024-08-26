from flask import Flask, render_template, jsonify, g, request
from database.db import get_db
from database.models import Stock, SentimentCompound, StockHistory, StockNews, DailyStockHistory, MonthlyStockHistory
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
# from parsing import currency_parser #, article_parser

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")


@app.route("/stock/<int:stock_id>", methods=["GET", "POST"])
def stock_detail(stock_id):
    period = request.args.get('period', 'daily')

    db = g.get('db', None)
    if db is None:
        db = next(get_db())
        g.db = db
    stock_compound = db.query(SentimentCompound).filter(SentimentCompound.stock_id == stock_id).first()
    positive = stock_compound.rise_probability
    negative = stock_compound.fall_probability
    stock = db.query(Stock).filter(Stock.id == stock_id).first()

    if period == 'daily':
        stock_history = db.query(DailyStockHistory).filter(DailyStockHistory.title == stock.title).all()
    elif period == 'monthly':
        stock_history = db.query(MonthlyStockHistory).filter(MonthlyStockHistory.title == stock.title).all()
    elif period == 'yearly':
        stock_history = db.query(StockHistory).filter(StockHistory.title == stock.title).all()
    else:
        return jsonify({'error': 'Invalid period specified'}), 400
    stock_history_data = [{
        'date': sh.date.isoformat(),
        'close': sh.close
    } for sh in stock_history]
    dates = []
    closes = []
    for index in stock_history_data:
        if period == "daily":
            dates.append(index['date'][11:])
        elif period == "monthly" or period == "yearly":
            dates.append(index['date'][:10])
        closes.append(index['close'])

    stock_news = db.query(StockNews).filter(StockNews.stock_id == stock_id).all()

    titles = []
    links = []
    summaries = []
    for data in stock_news:
        titles.append(data.title)
        links.append(data.link)
        summaries.append(data.summary)

    rises = [i.increase for i in stock_news]
    falls = [i.decrease for i in stock_news]
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'dates': dates, 'closes': closes})

    titles_summaries_rate = list(zip(titles, links, summaries, rises, falls))
    return render_template("stock.html",
                           stock=stock,
                           positive=positive,
                           negative=negative,
                           closes=closes,
                           dates=dates,
                           titles_summaries_rate=titles_summaries_rate)


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


# scheduler = BackgroundScheduler()
# scheduler.add_job(func=currency_parser.start_parsing, trigger="interval", seconds=10)
# scheduler.add_job(func=article_parser.create_directories, trigger="interval", minutes=30)
# scheduler.start()

# atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    app.run()
