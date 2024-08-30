from database.db import get_db
from database.models import HistoryToAnalyze


db = next(get_db())  # Get a database session
stocks = db.query(HistoryToAnalyze).all()

for i in stocks:
    print(i.title)