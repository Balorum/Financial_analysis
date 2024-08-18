import os
import bs4 as bs
import requests
from sqlalchemy import text
from random import choice
import yfinance as yf
from database.db import get_db
from database.models import StockNews, Stock, SentimentCompound
import article_analyzer


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
        company_name = row.find('span', attrs={'class': 'yf-ravs5v longName'}).text
        company_name = normalize_company_name(company_name)

        news = yf.Ticker(company_name).get_news()

        article_list = []
        for article in news:
            article_list.append(article["link"])

        news_dict[company_name] = article_list

    return news_dict


def get_articles_text():
    news_dict = get_companies_news()
    articles_dict = {}
    for company, links in news_dict.items():
        titles_list = []
        links_list = []
        summary_list = []
        rating_list = []
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
                    summary, rating = analyze_articles(company, p_list)
                    title = soup_news.find('h1', attrs={"id": "caas-lead-header-undefined"}).text
                    titles_list.append(title)
                    links_list.append(news_link)
                    summary_list.append(summary)
                    rating_list.append(rating)
        company_name = normalize_company_name(company)
        articles_dict[company_name] = [titles_list, links_list, summary_list, rating_list]
        fall_prob, rise_prob = calc_compound(rating_list)
        save_compound(fall_prob, rise_prob, company)
        break
    save_articles_news(articles_dict)


def calc_compound(rating_list):
    rise = 0
    fall = 0
    inform = 0
    for news_rate in rating_list:
        rise = rise + (news_rate["Increase Probability"] * news_rate["Informativeness"])
        fall = fall + (news_rate["Decrease Probability"] * news_rate["Informativeness"])
        inform = inform + news_rate["Informativeness"]
    fall_prob = fall/inform
    rise_prob = rise/inform
    return fall_prob, rise_prob


def save_compound(fall_prob, rise_prob, company):
    db = next(get_db())
    try:
        db.query(SentimentCompound).delete()
        db.commit()

        db.execute(text("ALTER SEQUENCE stock_compound_id_seq RESTART WITH 1"))
        db.commit()

        print("Updating stock compound...")
        stock_compounds = []
        stock = db.query(Stock).filter_by(title=company).first()
        if stock:
            compound = SentimentCompound(
                stock_id=stock.id,
                fall_probability=round(fall_prob, 2),
                rise_probability=round(rise_prob, 2),

            )
            stock_compounds.append(compound)
        else:
            print(f"Stock '{company}' not found in the Stock table")

        db.bulk_save_objects(stock_compounds)
        db.commit()

        print("Stock titles updated successfully.")
    except Exception as e:
        db.rollback()
        print(f"Failed to update stock titles: {e}")
    finally:
        db.close()


def normalize_company_name(company):
    company_name = company.replace(', Inc.', '')
    company_name = company_name.replace(' Inc.', '')

    return company_name


# def normalize_company(company):
#     dir_name = company
#     dir_name = dir_name.replace(" ", "_")
#     dir_name = dir_name.replace("-", "_")
#     dir_name = dir_name.replace(".", "_")
#     dir_name = dir_name.replace("&", "_")
#     return dir_name


# def create_directories():
#     print("Creating directories...")
#     if not os.path.exists("data"):
#         os.mkdir("data")
#         os.mkdir("data/stocks")
#         companies = get_companies_news().keys()
#         for company in companies:
#             dir_name = normalize_company(company)
#             os.mkdir(f"data/stocks/{dir_name}")
#     get_articles_text()


# def save_articles(company, rows, number):
#     company = normalize_company(company)
#     for root, dirs, files in os.walk(os.getcwd() + "/data/stocks"):
#         for dir_name in dirs:
#             folder_path = os.path.join(root, dir_name)
#             if company == dir_name:
#                 article = ""
#                 for row in rows:
#                     article += row.text
#                 try:
#                     file_path = folder_path + f"/{company}_article_{number}.txt"
#                     with open(file_path, "w", encoding='utf-8') as f:
#                         f.write(article)
#                 except Exception as e:
#                     print(f"Error while writing article {number} for {company}: {e}")

def analyze_articles(company, rows):
    article = ""
    for row in rows:
        article += row.text
    ready_article = article_analyzer.main(article, company)
    return ready_article


def save_articles_news(news_dict):
    db = next(get_db())
    try:
        db.query(StockNews).delete()
        db.commit()

        db.execute(text("ALTER SEQUENCE stock_news_id_seq RESTART WITH 1"))
        db.commit()

        print("Updating stock news...")

        stock_news = []
        for company, news_list in news_dict.items():
            for title, link, summary, rating in zip(news_list[0], news_list[1], news_list[2], news_list[3]):
                stock = db.query(Stock).filter_by(title=company).first()
                if stock:
                    one_news = StockNews(
                        stock_id=stock.id,
                        title=title,
                        link=link,
                        summary=summary,
                        decrease=rating["Decrease Probability"],
                        increase=rating["Increase Probability"],
                        informativeness=rating["Informativeness"]
                    )
                    stock_news.append(one_news)
                else:
                    print(f"Stock '{company}' not found in the Stock table")

        db.bulk_save_objects(stock_news)
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
        db.query(StockNews).delete()
        db.commit()

        db.execute(text("ALTER SEQUENCE stock_news_id_seq RESTART WITH 1"))
        db.commit()
        print("Stock titles deleted successfully.")
    except Exception as e:
        db.rollback()
        print("Failed to delete stock titles.")


get_articles_text()
