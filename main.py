from flask import Flask, render_template, jsonify, g, request
from database.db import get_db  # Importing the database connection function
from database.models import Stock, SentimentCompound, StockHistory, StockNews, DailyStockHistory, MonthlyStockHistory


# Initialize the Flask application
app = Flask(__name__)


def get_db_connection():
    """
        Establishes and returns a database connection from Flask's application context.
        If a connection does not exist, it creates a new one and stores it in the application context.

        Returns:
            db: The database connection object.
    """
    db = g.get('db', None)
    if db is None:
        db = next(get_db())
        g.db = db
    return db


@app.errorhandler(404)
def not_found_error(error):
    """
        Handles 404 Not Found errors by returning a JSON response with an error message.

        Args:
            error: The error object passed by Flask.

        Returns:
            Response: JSON response with a 404 status code and an error message.
    """
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(400)
def bad_request_error(error):
    """
        Handles 400 Bad Request errors by returning a JSON response with an error message.

        Args:
            error: The error object passed by Flask.

        Returns:
            Response: JSON response with a 400 status code and an error message.
    """
    return jsonify({'error': 'Bad request'}), 400


# Route for the homepage
@app.route("/", methods=["GET", "POST"])
def index():
    """
        Renders the homepage of the application.

        Returns:
            Response: The rendered HTML template for the homepage.
    """
    return render_template("index.html")


def get_stock_history(db, stock, period):
    """
        Fetches stock history data from the database based on the specified period.

        Args:
            db: The database connection object.
            stock: The stock object for which history is being fetched.
            period: The period for which stock history is requested ('daily', 'monthly', 'yearly').

        Returns:
            list: A list of stock history objects for the specified period.

        Raises:
            ValueError: If an invalid period is specified.
    """
    if period == 'daily':
        return db.query(DailyStockHistory).filter(DailyStockHistory.title == stock.title).all()
    elif period == 'monthly':
        return db.query(MonthlyStockHistory).filter(MonthlyStockHistory.title == stock.title).all()
    elif period == 'yearly':
        return db.query(StockHistory).filter(StockHistory.title == stock.title).all()
    else:
        raise ValueError("Invalid period specified")


def prepare_stock_history_data(stock_history, period):
    """
        Prepares stock history data for visualization by formatting dates and closing prices.

        Args:
            stock_history: A list of stock history objects.
            period: The period for which the data is being prepared ('daily', 'monthly', 'yearly').

        Returns:
            tuple: A tuple containing two lists: dates and closing prices.
    """
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
    return dates, closes


# Route for displaying details of a specific stock based on its ID
@app.route("/stock/<int:stock_id>", methods=["GET", "POST"])
def stock_detail(stock_id):
    """
        Displays detailed information about a specific stock, including historical data and news.

        Args:
            stock_id: The ID of the stock to display details for.

        Returns:
            Response: The rendered HTML template for the stock details page.
    """

    period = request.args.get('period', 'daily')  # Get the period parameter from the URL (default is 'daily')

    db = get_db_connection()  # Establish database connection if not already available

    # Fetch sentiment data for the specific stock
    stock_compound = db.query(SentimentCompound).filter(SentimentCompound.stock_id == stock_id).first()
    positive = stock_compound.rise_probability
    negative = stock_compound.fall_probability
    stock = db.query(Stock).filter(Stock.id == stock_id).first()

    # Fetch stock history data based on the selected period
    stock_history = get_stock_history(db, stock, period)

    # Prepare data for visualization: dates and closing prices
    dates, closes = prepare_stock_history_data(stock_history, period)

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
    """
        Fetches stock data for a specific stock and period, and returns it as JSON.

        Args:
            stock_id: The ID of the stock to fetch data for.

        Returns:
            Response: JSON response containing dates and closing prices.
    """

    period = request.args.get('period', 'daily')  # Get the period parameter from the URL (default is 'daily')

    db = get_db_connection()  # Establish database connection if not already available

    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        return jsonify({'error': 'Stock not found'}), 404

    stock_history = get_stock_history(db, stock, period)

    # Prepare data for JSON response: dates and closing prices
    dates, closes = prepare_stock_history_data(stock_history, period)

    return jsonify({'dates': dates, 'closes': closes})


# Route to fetch general stock data
@app.route("/data", methods=["GET", "POST"])
def data():
    """
        Fetches general data for all stocks and returns it as JSON.

        Returns:
            Response: JSON response containing general information about all stocks.
    """

    db = get_db_connection()  # Establish database connection if not already available

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
    """
        Closes the database connection when the application context ends.

        Args:
            exception: Optional exception object that may be passed when the context ends.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


if __name__ == "__main__":
    app.run()
