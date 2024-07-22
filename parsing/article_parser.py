import os
import bs4 as bs
from selenium.webdriver import Edge, EdgeOptions
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


os.chdir("C:\\Users\\remes\\PycharmProjects\\Financial_analysis")

base_link = "https://www.investing.com"
stocks_link = "https://www.investing.com/equities/trending-stocks"


def initialize_driver():
    options = EdgeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    driver = Edge(options=options)

    return driver


def get_stocks_page():

    stocks_dict = {}
    driver = initialize_driver()
    driver.get(stocks_link)
    time.sleep(5)
    soup = bs.BeautifulSoup(driver.page_source, 'html.parser')

    rows = soup.find('tbody', attrs={'class': "datatable-v2_body__8TXQk"}).find_all('tr')

    for row in rows:
        element = row.find('a')
        news_link = base_link + element.get('href')
        stocks_dict[element.text] = news_link

    driver.quit()

    return stocks_dict


def get_articles_link():
    stocks_dict = get_stocks_page()
    for key, value in stocks_dict.items():
        driver = initialize_driver()
        driver.get(value)
        time.sleep(5)
        soup = bs.BeautifulSoup(driver.page_source, 'html.parser')
        try:
            rows = (soup.find('ul', attrs={'data-test': "new-and-analysis-list"})
                    .find_all('li', attrs={'class': "border-[#E6E9EB] first:border-t border-b"}))
        except AttributeError as e:
            print(f"Error while parsing articles for {key}: {e}")
        finally:
            driver.quit()
        for number, row in enumerate(rows):
                element = row.find('a', attrs={'data-test': "article-title-link"})
                if "/pro/" not in element.get("href"):
                    news_link = base_link + element.get("href")
                    try:
                        get_articles_pages(key, news_link, number)
                    except Exception as e:
                        print(f"Error while processing article {number} for {key}: {e}")
                        continue


def normalize_company(company):
    dir_name = company[:-1]
    dir_name = dir_name.replace(" ", "_")
    dir_name = dir_name.replace("-", "_")
    dir_name = dir_name.replace(".", "_")
    return dir_name


def create_directories():
    print("Creating directories...")
    if not os.path.exists("data"):
        os.mkdir("data")
        os.mkdir("data/stocks")
        companies = get_stocks_page().keys()
        for company in companies:
            dir_name = normalize_company(company)
            os.mkdir(f"data/stocks/{dir_name}")
    get_articles_link()


def get_articles_pages(company, news_link, number):
    company = normalize_company(company)
    driver = initialize_driver()
    driver.get(news_link)
    time.sleep(5)
    soup = bs.BeautifulSoup(driver.page_source, 'html.parser')
    try:
        rows = (
            soup.find('div', attrs={'class': "article_WYSIWYG__O0uhw article_articlePage__UMz3q text-[18px] leading-8"})
            .find_all('p'))
    except AttributeError as e:
        print(f"Error while parsing article page for {company}: {e}")
    finally:
        driver.quit()
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


create_directories()
