import bs4 as bs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import text
from database.models import Stock, StockHistory
from database.db import get_db
import requests
import yfinance as yf
from datetime import datetime, timedelta

CURRENCY_LINK = "https://finance.yahoo.com/most-active/"


def get_page(link=CURRENCY_LINK):

    print("Opening the web page...")
    response = requests.get(link)
    soup = bs.BeautifulSoup(response.text, 'html.parser')
    return soup


def get_company_name(row):
    company_name = row.find('td', attrs={'class': 'Va(m) Ta(start) Px(10px) Fz(s)'}).text
    company_name = company_name.replace(', Inc.', '')
    company_name = company_name.replace(' Inc.', '')

    return company_name


def get_stock_name(row):
    return row.find('a', attrs={"data-test": "quoteLink"}).text


def get_currencies(page):
    try:
        print("Page loaded successfully. Parsing content...")

        rows = page.find('tbody').find_all('tr')
        if not rows:
            raise ValueError("No rows found in the table.")

        companies_dict = {}
        for row in rows:
            company_name = get_company_name(row)
            change_cell = row.find("span").text
            change_prc_cell = row.find("td", attrs={"aria-label": "% Change"}).text
            growth = True if change_cell[0] == "+" else False

            stock_name = get_stock_name(row)
            stock_history = yf.Ticker(stock_name).history()

            companies_dict[company_name] = {
                "last": round(stock_history["Close"].iloc[-1], 2),
                "high": round(stock_history["High"].iloc[-1], 2),
                "low": round(stock_history["Low"].iloc[-1], 2),
                "vol": round(stock_history["Volume"].iloc[-1]/1000000, 3),
                "change": change_cell[1:],
                "change_pct": change_prc_cell[1:-1],
                "growth": growth
            }
        print(f"Fetched data for {len(companies_dict)} companies.")
        return companies_dict

    except Exception as e:
        print(f"Error fetching currencies: {e}")
        return {}


def get_historical_data(page):
    try:
        print("Page for historical data loaded successfully. Parsing content...")

        rows = page.find('tbody').find_all('tr')
        if not rows:
            raise ValueError("No rows found in the table.")

        company_history = {}
        for row in rows:
            stock_name = get_stock_name(row)
            company_name = get_company_name(row)
            ticker = yf.Ticker(stock_name)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            hist_data = ticker.history(start=start_date, end=end_date)
            historical_prices = []

            for date, row in hist_data.iterrows():
                historical_prices.append({
                    "title": company_name,
                    "open": round(row["Open"], 2),
                    "high": round(row["High"], 2),
                    "low": round(row["Low"], 2),
                    "close": round(row["Close"], 2),
                    "volume": round(row["Volume"], 2),
                    "date": date.date(),
                })
            company_history[company_name] = historical_prices
        return company_history

    except Exception as e:
        print(f"Error fetching currencies: {e}")
        return {}


def update_companies(page):
    db = next(get_db())
    try:
        db.query(Stock).delete()
        db.commit()

        db.execute(text("ALTER SEQUENCE stocks_id_seq RESTART WITH 1"))
        db.commit()

        print("Fetching currencies...")
        companies_dict = get_currencies(page)
        if not companies_dict:
            raise Exception("Failed to fetch company data")

        stocks = []
        for name, value in companies_dict.items():
            stock = Stock(title=name,
                          last=value['last'],
                          high=value['high'],
                          low=value['low'],
                          volume=value['vol'],
                          change=value['change'],
                          change_pct=value['change_pct'],
                          growth=value['growth'])
            stocks.append(stock)

        db.bulk_save_objects(stocks)
        db.commit()
        print("Companies updated successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error updating companies: {e}")

    finally:
        db.close()


def update_companies_history(page):
    db = next(get_db())
    try:
        # Clear the Stock table
        db.query(StockHistory).delete()
        db.commit()

        db.execute(text("ALTER SEQUENCE stocks_history_id_seq RESTART WITH 1"))
        db.commit()

        print("Fetching currencies...")
        companies_dict = get_historical_data(page)
        if not companies_dict:
            raise Exception("Failed to fetch company data")

        stocks_hist = []
        for name, values in companies_dict.items():
            for value in values:
                stock_hist = StockHistory(title=name,
                                          open=value['open'],
                                          high=value['high'],
                                          low=value['low'],
                                          close=value['close'],
                                          volume=value['volume'],
                                          date=value['date'])
                stocks_hist.append(stock_hist)

        db.bulk_save_objects(stocks_hist)
        db.commit()
        print("Companies updated successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error updating companies: {e}")

    finally:
        db.close()


def start_parsing():
    page = get_page()
    update_companies(page=page)


def start_parsing_history():
    page = get_page()
    update_companies_history(page=page)

    
start_parsing()