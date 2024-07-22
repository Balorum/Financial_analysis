from sqlalchemy import Column, Integer, String, Boolean, Float, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Stock(Base):
    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True)
    title = Column(String(50), nullable=False)
    last = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    change = Column(Float, nullable=False)
    change_pct = Column(Float, nullable=False)
    growth = Column(Boolean, nullable=False)
    date = Column(DateTime, nullable=False, default=func.now())
    # Define a relationship to the StockSentiment table
    sentiments = relationship("StockSentiment", back_populates="stock")


class StockSentiment(Base):
    __tablename__ = "stock_sentiments"
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    positives = Column(Integer, nullable=False, default=0)
    negatives = Column(Integer, nullable=False, default=0)

    # Define a relationship to the Stock table
    stock = relationship("Stock", back_populates="sentiments")