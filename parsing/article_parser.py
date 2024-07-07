import os
import bs4 as bs
import requests


os.chdir("C:\\Users\\remes\\PycharmProjects\\Financial_analysis")

base_link = "https://www.investing.com"
stocks_link = "https://www.investing.com/equities/trending-stocks"


def get_stocks_page():
    stocks_dict = {}
    page = requests.get(stocks_link)
    soup = bs.BeautifulSoup(page.content, 'html.parser')

    rows = soup.find('tbody', attrs={'class': "datatable-v2_body__8TXQk"}).find_all('tr')

    for row in rows:
        element = row.find('a')
        news_link = base_link + element.get('href')
        stocks_dict[element.text] = news_link

    return stocks_dict


def get_articles_link():
    stocks_dict = get_stocks_page()
    for key, value in stocks_dict.items():
        page = requests.get(value)
        soup = bs.BeautifulSoup(page.content, 'html.parser')
        rows = (soup.find('ul', attrs={'data-test': "new-and-analysis-list"})
                .find_all('li', attrs={'class': "border-[#E6E9EB] first:border-t border-b"}))
        for number, row in enumerate(rows):
            # if row.find('svg') is not None:
                element = row.find('a', attrs={'data-test': "article-title-link"})
                if "/pro/" not in element.get("href"):
                    news_link = base_link + element.get("href")
                    get_articles_pages(key, news_link, number)


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


def get_articles_pages(company, news_link, number):
    company = normalize_company(company)
    page = requests.get(news_link)
    soup = bs.BeautifulSoup(page.content, 'html.parser')
    rows = (soup.find('div', attrs={'class': "article_WYSIWYG__O0uhw article_articlePage__UMz3q text-[18px] leading-8"})
            .find_all('p'))
    for root, dirs, files in os.walk(os.getcwd() + "/data/stocks"):
        for dir_name in dirs:
            folder_path = os.path.join(root, dir_name)
            if company == dir_name:
                article = ""
                for row in rows:
                    article += row.text
                print(folder_path + f"/{company}_article_{number}.txt")
                with open(folder_path + f"/{company}_article_{number}.txt", "w", encoding='utf-8') as f:
                    f.write(article)


if __name__ == "__main__":
    create_directories()
    get_articles_link()
