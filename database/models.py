from sqlalchemy import Column, Integer, String, Boolean, Float, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Stock(Base):
    __tablename__ = "stocks"
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    last = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    change = Column(Float, nullable=False)
    change_pct = Column(Float, nullable=False)
    growth = Column(Boolean, nullable=False)
    date = Column(DateTime, nullable=False, default=func.now())

    sentiments = relationship("StockSentiment", back_populates="stock")
    titles = relationship("StockTitle", back_populates="stock")


class StockHistory(Base):
    __tablename__ = "stocks_history"
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)


class StockSentiment(Base):
    __tablename__ = "stock_sentiments"
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    positives = Column(Integer, nullable=False, default=0)
    negatives = Column(Integer, nullable=False, default=0)

    stock = relationship("Stock", back_populates="sentiments")


class StockTitle(Base):
    __tablename__ = "stock_titles"
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    title = Column(String(250), nullable=False)
    link = Column(String(300), nullable=False)

    stock = relationship("Stock", back_populates="titles")
