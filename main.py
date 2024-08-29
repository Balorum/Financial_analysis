from flask import Flask, render_template, jsonify, g, request
from database.db import get_db  # Importing the database connection function
from database.models import Stock, SentimentCompound, StockHistory, StockNews, DailyStockHistory, MonthlyStockHistory
from apscheduler.schedulers.background import BackgroundScheduler  # Scheduler for background tasks
import atexit  # To ensure the scheduler shuts down cleanly on exit

# Initialize the Flask application
app = Flask(__name__)


def get_db_connection():
    db = g.get('db', None)
    if db is None:
        db = next(get_db())
        g.db = db
    return db


# Route for the homepage
@app.route("/", methods=["GET", "POST"])
def index():
    # Render the index.html template
    return render_template("index.html")


# Route for displaying details of a specific stock based on its ID
@app.route("/stock/<int:stock_id>", methods=["GET", "POST"])
def stock_detail(stock_id):
    # Get the period parameter from the URL (default is 'daily')
    period = request.args.get('period', 'daily')

    # Establish database connection if not already available
    db = get_db_connection()

    # Fetch sentiment data for the specific stock
    stock_compound = db.query(SentimentCompound).filter(SentimentCompound.stock_id == stock_id).first()
    positive = stock_compound.rise_probability
    negative = stock_compound.fall_probability
    stock = db.query(Stock).filter(Stock.id == stock_id).first()

    # Fetch stock history data based on the selected period
    if period == 'daily':
        stock_history = db.query(DailyStockHistory).filter(DailyStockHistory.title == stock.title).all()
    elif period == 'monthly':
        stock_history = db.query(MonthlyStockHistory).filter(MonthlyStockHistory.title == stock.title).all()
    elif period == 'yearly':
        stock_history = db.query(StockHistory).filter(StockHistory.title == stock.title).all()
    else:
        return jsonify({'error': 'Invalid period specified'}), 400

    # Prepare data for visualization: dates and closing prices
    stock_history_data = [{
        'date': sh.date.isoformat(),
        'close': sh.close
    } for sh in stock_history]
    dates = []
    closes = []
    for index in stock_history_data:
        if period == "daily":
            dates.append(index['date'][11:])  # Use only the time part for daily data
        elif period == "monthly" or period == "yearly":
            dates.append(index['date'][:10])  # Use only the date part for monthly/yearly data
        closes.append(index['close'])

    # Fetch news related to the stock
    stock_news = db.query(StockNews).filter(StockNews.stock_id == stock_id).all()

    # Prepare news data for rendering
    titles = []
    links = []
    summaries = []
    for data in stock_news:
        titles.append(data.title)
        links.append(data.link)
        summaries.append(data.summary)

    # Prepare sentiment analysis data for display
    rises = [i.increase for i in stock_news]
    falls = [i.decrease for i in stock_news]

    titles_summaries_rate = list(zip(titles, links, summaries, rises, falls))

    # Render the stock details template with the data
    return render_template("stock.html",
                           stock=stock,
                           positive=positive,
                           negative=negative,
                           closes=closes,
                           dates=dates,
                           titles_summaries_rate=titles_summaries_rate)


# Route to fetch stock data for AJAX requests
@app.route("/stock_data/<int:stock_id>", methods=["GET"])
def stock_data(stock_id):
    # Get the period parameter from the URL (default is 'daily')
    period = request.args.get('period', 'daily')

    # Establish database connection if not already available
    db = get_db_connection()

    # Fetch stock data from the database
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        return jsonify({'error': 'Stock not found'}), 404

    # Fetch stock history data based on the selected period
    if period == 'daily':
        stock_history = db.query(DailyStockHistory).filter(DailyStockHistory.title == stock.title).all()
    elif period == 'monthly':
        stock_history = db.query(MonthlyStockHistory).filter(MonthlyStockHistory.title == stock.title).all()
    elif period == 'yearly':
        stock_history = db.query(StockHistory).filter(StockHistory.title == stock.title).all()
    else:
        return jsonify({'error': 'Invalid period specified'}), 400

    # Prepare data for JSON response: dates and closing prices
    stock_history_data = [{
        'date': sh.date.isoformat(),
        'close': sh.close
    } for sh in stock_history]

    dates = []
    closes = []
    for index in stock_history_data:
        if period == "daily":
            dates.append(index['date'][11:])  # Use only the time part for daily data
        elif period == "monthly" or period == "yearly":
            dates.append(index['date'][:10])  # Use only the date part for monthly/yearly data
        closes.append(index['close'])

    return jsonify({'dates': dates, 'closes': closes})


# Route to fetch general stock data
@app.route("/data", methods=["GET", "POST"])
def data():
    # Establish database connection if not already available
    db = get_db_connection()

    # Fetch all stocks data
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


# Close the database connection when the application context ends
@app.teardown_appcontext
def shutdown_session(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Background job scheduler setup (commented out)
# scheduler = BackgroundScheduler()
# scheduler.add_job(func=currency_parser.start_parsing, trigger="interval", seconds=10)
# scheduler.add_job(func=article_parser.create_directories, trigger="interval", minutes=30)
# scheduler.start()

# Ensure the scheduler shuts down cleanly on exit
# atexit.register(lambda: scheduler.shutdown())


# Run the Flask app if this script is executed directly
if __name__ == "__main__":
    app.run()
