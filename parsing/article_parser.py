import os
import logging
import bs4 as bs
import requests
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from random import choice
import yfinance as yf
from requests.exceptions import RequestException
from database.db import get_db
from database.models import StockNews, Stock, SentimentCompound
import article_analyzer

# os.chdir("C:\\Users\\remes\\PycharmProjects\\Financial_analysis")

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("logs/article_parser.log"),  # Log to a file
                        logging.StreamHandler()  # Also log to console
                    ]
                    )


header_1 = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
header_2 = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"}
header_3 = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36 OPR/38.0.2220.41"}
header_4 = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"}
header_5 = {"User-Agent": "Mozilla/5.0 (Linux; U; Linux i674 x86_64; en-US) AppleWebKit/600.12 (KHTML, like Gecko) Chrome/53.0.2954.236 Safari/602"}


HEADERS = [header_1, header_2, header_3, header_4, header_5]


def get_companies_news():
    db = next(get_db())
    logging.info(f"Query the database to get all current stocks...")
    stocks = db.query(Stock).all()
    if not stocks:
        logging.error("No stocks found.")
    news_dict = {}

    for stock in stocks:
        try:
            news = yf.Ticker(stock.title).get_news()
            article_list = []
            for article in news:
                article_list.append(article["link"])

            news_dict[stock.title] = article_list
        except Exception as e:
            logging.error(f"Error fetching news for {stock.title}: {e}")

    return news_dict


def fetch_article_content():
    news_dict = get_companies_news()
    articles_dict = {}
    for company, links in news_dict.items():
        logging.info(f"Analyzing company {company} started")
        titles_list = []
        links_list = []
        summary_list = []
        rating_list = []
        for news_link in links:
            try:
                response_news = requests.get(news_link, headers=choice(HEADERS), timeout=40)
                soup_news = bs.BeautifulSoup(response_news.text, 'html.parser')

                if soup_news.find('a', attrs={"class": "caas-readmore caas-readmore-collapse"}):
                    continue

                article_div = soup_news.find("div", attrs={
                        "class": "morpheusGridBody col-neofull-offset-3-span-8 col-neolg-offset-3-span-8 col-neomd-offset-1-span-6 col-neosm-offset-2-span-4"})
                if not article_div:
                    continue

                paragraphs = article_div.find_all('p')
                if len(paragraphs) < 2:
                    continue

                summary, rating = analyze_articles(company, paragraphs)

                title = soup_news.find('h1', attrs={"id": "caas-lead-header-undefined"})
                if title:
                    titles_list.append(title.text)
                    links_list.append(news_link)
                    summary_list.append(summary)
                    rating_list.append(rating)
            except Exception as e:
                logging.error(f"While analyzing company {company} on {news_link} got exception {e}")
        logging.info(f"Analyzing company {company} finished")
        company_name = normalize_company_name(company)
        articles_dict[company_name] = [titles_list, links_list, summary_list, rating_list]
    save_compound(articles_dict)
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


def save_compound(article_dict):
    db = next(get_db())
    try:
        db.query(SentimentCompound).delete()
        db.commit()

        db.execute(text("ALTER SEQUENCE stock_compound_id_seq RESTART WITH 1"))
        db.commit()

        logging.info("Updating stock compound...")
        stock_compounds = []
        for company, values_list in article_dict.items():
            stock = db.query(Stock).filter_by(title=company).first()
            if stock:
                fall_prob, rise_prob = calc_compound(values_list[3])
                compound = SentimentCompound(
                    stock_id=stock.id,
                    fall_probability=round(fall_prob, 2),
                    rise_probability=round(rise_prob, 2),

                )
                stock_compounds.append(compound)
            else:
                logging.warning(f"Stock '{company}' not found in the Stock table")

        db.bulk_save_objects(stock_compounds)
        db.commit()

        logging.info("Stock compounds updated successfully.")
    except SQLAlchemyError as e:
        db.rollback()
        logging.error(f"Failed to update stock compounds: {e}")
    finally:
        db.close()


def normalize_company_name(company):
    company_name = company.replace(', Inc.', '')
    company_name = company_name.replace(' Inc.', '')

    return company_name


def analyze_articles(company, rows):
    article = ""
    for row in rows:
        article += row.text
    summary, rating = article_analyzer.main(article, company)
    return summary, rating


def save_articles_news(news_dict):
    db = next(get_db())
    try:
        logging.info("Delete previous news...")
        db.query(StockNews).delete()
        db.commit()

        db.execute(text("ALTER SEQUENCE stock_news_id_seq RESTART WITH 1"))
        db.commit()

        logging.info("Updating stock news...")

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
                    logging.warning(f"Stock '{company}' not found in the Stock table")

        db.bulk_save_objects(stock_news)
        db.commit()

        logging.info("Stock news updated successfully.")
    except SQLAlchemyError as e:
        db.rollback()
        logging.error(f"Failed to update stock news: {e}")
    finally:
        db.close()


def clear_news_db():
    db = next(get_db())
    try:
        logging.info("Trying to delete stock news...")
        db.query(StockNews).delete()
        db.commit()

        db.execute(text("ALTER SEQUENCE stock_news_id_seq RESTART WITH 1"))
        db.commit()
        logging.info("Stock news deleted successfully.")
    except SQLAlchemyError as e:
        db.rollback()
        logging.error(f"Failed to delete stock titles: {e}")


fetch_article_content()
