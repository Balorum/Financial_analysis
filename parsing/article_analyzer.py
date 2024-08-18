import nltk
import pandas as pd
import numpy as np
import os
import re
from time import sleep
from sqlalchemy import text
from database.models import Stock, StockNews
from database.db import get_db

from nltk.corpus import stopwords
nltk.download('vader_lexicon')
nltk.download('punkt')
nltk.download('stopwords')

import vertexai
from vertexai.generative_models import GenerativeModel

project_id = "phonic-obelisk-431915-c8"

vertexai.init(project=project_id, location="europe-west2")

model = GenerativeModel("gemini-1.5-flash-001")


stop_words = set(stopwords.words("english"))
articles_list = []


def delete_superfluous(article):
    pattern_1 = r'\(\w+\)'
    article = re.sub(pattern_1, '', article)
    pattern_2 = r'\(NASDAQ: \w+\)'
    article = re.sub(pattern_2, '', article)
    return article


def delete_punctuation(article):
    pattern = r'[^\w\s]'
    article = re.sub(pattern, '', article)
    return article


def sentence_tokenization(sentence):
    article_word_list = nltk.tokenize.word_tokenize(sentence)
    return article_word_list


def article_tokenization(article):
    sentences = nltk.tokenize.sent_tokenize(article)
    return sentences


def delete_stop_words(article_list):
    global stop_words
    processed_article = [word for word in article_list if word.lower() not in stop_words]
    return processed_article


def request_processing(request):
    response = model.generate_content(request)
    return response.text

def text_processing(article_text):
    words_list = []
    sentences_list = []
    sentences = article_tokenization(article_text)
    for sentence in sentences:
        sentence = delete_superfluous(sentence)
        sentence = delete_punctuation(sentence)
        tokenized_sentence = sentence_tokenization(sentence)
        without_base_sw = delete_stop_words(tokenized_sentence)
        words_list.append(without_base_sw)
    for word_list in words_list:
        sentence = ' '.join(word_list)
        sentence = sentence.capitalize()
        sentence = re.sub(r'([.!?])(\w)', r'\1 \2', sentence)
        sentences_list.append(sentence)
    articles_list.append(sentences_list)
    processed_article = ". ".join(articles_list[0])
    return processed_article


def ai_analyzer(article, company_name):
    request = (f"I have several financial articles about {company_name}. I want you to analyze each one in turn "
               f"and provide the result in the form of: 3 sentences that best describe what the article is about, "
               f"and also I want you to provide a forecast based on this news, with what chance the stock price will "
               f"go up and with what chance it will go down in the format: '(decrease 30% | increase 70%)' - the total"
               f" should be 100%. And also how useful is this article for predicting the rise/fall of a stock in the "
               f"format '(Informativeness: 50%)'. Here is one of the articles: \n\n")

    full_request = request + article
    response = request_processing(full_request)
    print("Artificial intelligence begins to analyze the article...")
    sleep(30)
    return response


def get_rate(summary):
    print("Artificial intelligence begins to analyze the informativeness "
          "of an article and the probability of growth/fall of stock")
    forecast_pattern_1 = re.compile(r'\(decrease (\d+%) \| increase (\d+%)\)')
    forecast_pattern_2 = re.compile(r'\(increase (\d+%) \| decrease (\d+%)\)')
    informativeness_pattern = re.compile(r'\(informativeness: (\d+%)\)')

    lower_summary = summary.lower()
    forecasts = forecast_pattern_1.findall(lower_summary)
    if forecasts == []:
        swap = forecast_pattern_2.findall(lower_summary)
        forecasts = [(swap[0][1], swap[0][0])]
        if swap == []:
            forecasts = ["50%", "50%"]
    informativeness = informativeness_pattern.findall(lower_summary)
    if informativeness == []:
        informativeness = 50
    else:
        informativeness = int(informativeness[0].replace('%', ''))

    decrease = int(forecasts[0][0].replace('%', ''))
    increase = int(forecasts[0][1].replace('%', ''))

    print(f"informativeness: {informativeness}")
    print(f"decrease: {decrease}")
    print(f"increase: {increase}")

    data = {
        'Decrease Probability': decrease,
        'Increase Probability': increase,
        'Informativeness': informativeness,
    }
    return data


def response_processing(response):
    patterns_to_remove = [
        r"\*\*.*?\*\*|##.*?##', '"
        r"\n\s*\n', '\n\n",
        r"##.*",
        r'\(.*?\)',
        r'\b\d+\.',
        r'\*',
    ]

    for pattern in patterns_to_remove:
        response = re.sub(pattern, '', response)
    response = re.sub(r'\n+', '\n', response)
    response = response.strip()
    return response


def main(article, company_name):
    processed_article = text_processing(article)
    summary = ai_analyzer(processed_article, company_name)
    rating = get_rate(summary)
    ready_article = response_processing(summary)
    return ready_article, rating
