from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from database.models import Stock, StockHistory, DailyStockHistory, MonthlyStockHistory, StockNews, SentimentCompound
from database.db import get_db

db = next(get_db())

# db.query(Stock).delete()
# db.commit()

result = db.query(StockHistory).delete()

print(result)
