import os
import bs4 as bs
import requests
from sqlalchemy import text
from random import choice
import yfinance as yf
from database.db import get_db
from database.models import StockTitle, Stock


os.chdir("C:\\Users\\remes\\PycharmProjects\\Financial_analysis")

header_1 = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
header_2 = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"}
header_3 = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36 OPR/38.0.2220.41"}
header_4 = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"}
header_5 = {"User-Agent": "Mozilla/5.0 (Linux; U; Linux i674 x86_64; en-US) AppleWebKit/600.12 (KHTML, like Gecko) Chrome/53.0.2954.236 Safari/602"}
header_6 = {"User-Agent": "Mozilla/5.0 (compatible; MSIE 9.0; Windows; Windows NT 6.1; x64 Trident/5.0)"}
header_7 = {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 10.1; x64) AppleWebKit/602.31 (KHTML, like Gecko) Chrome/48.0.3670.320 Safari/535.5 Edge/17.36249"}
header_8 = {"User-Agent": "Mozilla/5.0 (compatible; MSIE 10.0; Windows; Windows NT 6.0; Trident/6.0)"}
header_9 = {"User-Agent": "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 9_9_3; en-US) Gecko/20100101 Firefox/58.5"}
header_10 = {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 10.5; x64) AppleWebKit/601.3 (KHTML, like Gecko) Chrome/47.0.2829.299 Safari/600.2 Edge/15.98741"}

headers = [header_1, header_2, header_3, header_4, header_5, header_6, header_7, header_8, header_9, header_10]

STOCKS_RESPONSE = requests.get("https://finance.yahoo.com/most-active/", headers=choice(headers), timeout=10)


def get_companies_news(response=STOCKS_RESPONSE):

    soup = bs.BeautifulSoup(response.text, 'html.parser')

    rows = soup.find('tbody').find_all('tr')
    news_dict = {}

    for row in rows:
        company_name = row.find('td', attrs={'class': 'Va(m) Ta(start) Px(10px) Fz(s)'}).text
        company_name = company_name.replace(', Inc.', '')
        company_name = company_name.replace(' Inc.', '')

        news = yf.Ticker(company_name).get_news()

        article_list = []
        for article in news:
            article_list.append(article["link"])

        news_dict[company_name] = article_list

    return news_dict


def get_articles_text():
    news_dict = get_companies_news()
    titles_dict = {}
    for company, links in news_dict.items():
        number = 1
        titles_list = []
        links_list = []
        for news_link in links:
            response_news = requests.get(news_link, headers=choice(headers), timeout=10)
            soup_news = bs.BeautifulSoup(response_news.text, 'html.parser')
            rows = soup_news.find('a', attrs={"class": "caas-readmore caas-readmore-collapse"})
            if rows:
                continue
            else:
                rows = soup_news.find("div", attrs={
                    "class": "morpheusGridBody col-neofull-offset-3-span-8 col-neolg-offset-3-span-8 col-neomd-offset-1-span-6 col-neosm-offset-2-span-4"})
                if rows:
                    p_list = rows.find_all('p')
                    if len(p_list) < 2:
                        continue
                    save_articles(company, p_list, number)
                    title = soup_news.find('h1', attrs={"id": "caas-lead-header-undefined"}).text
                    titles_list.append(title)
                    links_list.append(news_link)
                    number += 1
        company_name = normalize_company_name(company)
        titles_dict[company_name] = [titles_list, links_list]
    save_articles_titles(titles_dict)


def normalize_company_name(company):
    company_name = company.replace(', Inc.', '')
    company_name = company_name.replace(' Inc.', '')

    return company_name


def normalize_company(company):
    dir_name = company
    dir_name = dir_name.replace(" ", "_")
    dir_name = dir_name.replace("-", "_")
    dir_name = dir_name.replace(".", "_")
    dir_name = dir_name.replace("&", "_")
    return dir_name


def create_directories():
    print("Creating directories...")
    if not os.path.exists("data"):
        os.mkdir("data")
        os.mkdir("data/stocks")
        companies = get_companies_news().keys()
        for company in companies:
            dir_name = normalize_company(company)
            os.mkdir(f"data/stocks/{dir_name}")
    get_articles_text()


def save_articles(company, rows, number):
    company = normalize_company(company)
    for root, dirs, files in os.walk(os.getcwd() + "/data/stocks"):
        for dir_name in dirs:
            folder_path = os.path.join(root, dir_name)
            if company == dir_name:
                article = ""
                for row in rows:
                    article += row.text
                try:
                    file_path = folder_path + f"/{company}_article_{number}.txt"
                    with open(file_path, "w", encoding='utf-8') as f:
                        f.write(article)
                except Exception as e:
                    print(f"Error while writing article {number} for {company}: {e}")


def save_articles_titles(titles_dict):
    db = next(get_db())
    try:
        db.query(StockTitle).delete()
        db.commit()

        db.execute(text("ALTER SEQUENCE stock_titles_id_seq RESTART WITH 1"))
        db.commit()

        print("Updating stock titles...")

        stock_titles = []
        for company, title_list in titles_dict.items():
            for title, link in zip(title_list[0], title_list[1]):
                stock = db.query(Stock).filter_by(title=company).first()
                if stock:
                    stock_title = StockTitle(
                        stock_id=stock.id,
                        title=title,
                        link=link
                    )
                    stock_titles.append(stock_title)
                else:
                    print(f"Stock '{company}' not found in the Stock table")

        db.bulk_save_objects(stock_titles)
        db.commit()

        print("Stock titles updated successfully.")
    except Exception as e:
        db.rollback()
        print(f"Failed to update stock titles: {e}")
    finally:
        db.close()


def clear_titles_db():
    db = next(get_db())
    try:
        print("Trying to delete stock titles...")
        db.query(StockTitle).delete()
        db.commit()

        db.execute(text("ALTER SEQUENCE stock_titles_id_seq RESTART WITH 1"))
        db.commit()
        print("Stock titles deleted successfully.")
    except Exception as e:
        db.rollback()
        print("Failed to delete stock titles.")


create_directories()
