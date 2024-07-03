import bs4 as bs
import requests
from database.models import Stock
from database.db import get_db
from sqlalchemy import text

web_sites = {
    "investing.com": "https://www.investing.com/",
    "AIER": "https://www.aier.org/articles/",
    "Financial_Times": "https://www.ft.com/markets"
}

currency_link = "https://www.investing.com/equities/trending-stocks"


def get_currencies(link=currency_link):

    page = requests.get(link)
    soup = bs.BeautifulSoup(page.content, 'html.parser')

    rows = soup.find('tbody', attrs={'class': "datatable-v2_body__8TXQk"}).find_all('tr')

    companies_dict = {}

    for row in rows:
        company_name = row.find('span', attrs={'class': 'block overflow-hidden text-ellipsis whitespace-nowrap'}).text
        data_cells = row.find_all('td', attrs={
            'class': "datatable-v2_cell__IwP1U dynamic-table-v2_col-other__zNU4A text-right rtl:text-right"})
        change_cell = row.find_all('td', attrs={"style": "--cell-display:flex;--cell-positions:chg"})[0].text
        change_prc_cell = row.find_all('td', attrs={"style": "--cell-display:flex;--cell-positions:chg-pct"})[0].text
        growth = True if change_prc_cell.startswith('+') else False

        change_cell, change_prc_cell = change_cell[1:], change_prc_cell[1:-1]
        volume = float(data_cells[3].text[:-1]) if data_cells[3].text.endswith('M') else float(data_cells[3].text[:-1])/1000
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

    return companies_dict


def update_companies():

    db = next(get_db())

    try:
        # Clear the Stock table
        db.query(Stock).delete()
        db.commit()

        # Reset the ID sequence
        db.execute(text("ALTER SEQUENCE stocks_id_seq RESTART WITH 1"))
        db.commit()

        companies_dict = get_currencies()
        stocks = []
        for name, values in companies_dict.items():
            stock = Stock(title=name,
                          last=values['last'],
                          high=values['high'],
                          low=values['low'],
                          volume=values['vol'],
                          change=values['change'],
                          change_pct=values['change_pct'],
                          growth=values['growth'])
            stocks.append(stock)

        db.bulk_save_objects(stocks)

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Error updating companies: {e}")
    finally:
        db.close()
