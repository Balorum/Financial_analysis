import bs4 as bs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import text
from database.models import Stock
from database.db import get_db
import time

CURRENCY_LINK = "https://www.investing.com/equities/trending-stocks"


def get_driver():
    options = Options()
    options.add_argument("--enable-automation")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    # options.add_argument("--headless")  # Commented out headless mode for debugging
    driver = webdriver.Edge(options=options)
    return driver


def get_currencies(driver, link=CURRENCY_LINK):
    try:
        print("Opening the web page...")
        driver.get(link)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "datatable-v2_body__8TXQk")))
        print("Page loaded successfully. Parsing content...")
        soup = bs.BeautifulSoup(driver.page_source, 'html.parser')

        rows = soup.find('tbody', attrs={'class': "datatable-v2_body__8TXQk"}).find_all('tr')
        if not rows:
            raise ValueError("No rows found in the table.")

        companies_dict = {}
        for row in rows:
            company_name = row.find('span',
                                    attrs={'class': 'block overflow-hidden text-ellipsis whitespace-nowrap'}).text
            data_cells = row.find_all('td', attrs={
                'class': "datatable-v2_cell__IwP1U dynamic-table-v2_col-other__zNU4A text-right rtl:text-right"})
            change_cell = row.find_all('td', attrs={"style": "--cell-display:flex;--cell-positions:chg"})[0].text
            change_prc_cell = row.find_all('td', attrs={"style": "--cell-display:flex;--cell-positions:chg-pct"})[
                0].text

            growth = True if change_prc_cell.startswith('+') else False

            change_cell, change_prc_cell = change_cell[1:], change_prc_cell[1:-1]
            volume = float(data_cells[3].text[:-1]) if data_cells[3].text.endswith('M') else float(
                data_cells[3].text[:-1]) / 1000
            data_values = [cell.text.replace(",", "") for cell in data_cells]

            companies_dict[company_name] = {
                "last": float(data_values[0]),
                "high": float(data_values[1]),
                "low": float(data_values[2]),
                "vol": volume,
                "change": change_cell,
                "change_pct": change_prc_cell,
                "growth": growth
            }
        print(f"Fetched data for {len(companies_dict)} companies.")
        return companies_dict

    except Exception as e:
        print(f"Error fetching currencies: {e}")
        return {}


def update_companies():
    db = next(get_db())
    driver = get_driver()
    try:
        # Clear the Stock table
        db.query(Stock).delete()
        db.commit()

        # Reset the ID sequence
        db.execute(text("ALTER SEQUENCE stocks_id_seq RESTART WITH 1"))
        db.commit()

        print("Fetching currencies...")
        companies_dict = get_currencies(driver)
        if not companies_dict:
            raise Exception("Failed to fetch company data")

        stocks = []
        for name, values in companies_dict.items():
            stock = Stock(title=name,
                          last=values['last'],
                          high=values['high'],
                          low=values['low'],
                          volume=round(values['vol'], 3),
                          change=values['change'],
                          change_pct=values['change_pct'],
                          growth=values['growth'])
            stocks.append(stock)

        db.bulk_save_objects(stocks)
        db.commit()
        print("Companies updated successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error updating companies: {e}")

    finally:
        db.close()
        driver.quit()


update_companies()
