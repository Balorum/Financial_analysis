import nltk
import os
import re
from time import sleep
import logging

from nltk.corpus import stopwords
nltk.download('vader_lexicon')
nltk.download('punkt')
nltk.download('stopwords')

import vertexai
from vertexai.generative_models import GenerativeModel

# os.chdir("C:\\Users\\remes\\PycharmProjects\\Financial_analysis")

logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more verbose output
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/article_analysis.log"),  # Log to a file
        logging.StreamHandler()  # Also log to console
    ]
)

project_id = "phonic-obelisk-431915-c8"
vertexai.init(project=project_id, location="europe-west2")

MODELS = []

stop_words = set(stopwords.words("english"))

SUPERFLUOUS_PATTERN_1 = re.compile(r'\(\w+\)')
SUPERFLUOUS_PATTERN_2 = re.compile(r'\(NASDAQ: \w+\)')
PUNCTUATION_PATTERN = re.compile(r'[^\w\s]')
FORECAST_PATTERN_1 = re.compile(r'\(decrease (\d+%) \| increase (\d+%)\)')
FORECAST_PATTERN_2 = re.compile(r'\(increase (\d+%) \| decrease (\d+%)\)')
INFORMATIVENESS_PATTERN = re.compile(r'\(informativeness: (\d+%)\)')


def create_models():
    logging.info("Creating AI models...")
    model_1 = GenerativeModel("gemini-1.5-flash-001")
    model_2 = GenerativeModel("gemini-1.5-flash-001")
    model_3 = GenerativeModel("gemini-1.5-flash-001")
    return [model_1, model_2, model_3]


def delete_superfluous(article):
    article = SUPERFLUOUS_PATTERN_1.sub('', article)
    article = SUPERFLUOUS_PATTERN_2.sub('', article)
    return article


def delete_punctuation(article):
    return PUNCTUATION_PATTERN.sub('', article)


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
    global MODELS

    if not MODELS:
        MODELS = create_models()

    max_retries = 6
    delay = 10
    backoff_factor = 5

    for attempt in range(max_retries):
        model = MODELS.pop()
        logging.info(f"Attempt {attempt + 1}: Sending request to AI model for analysis...")
        try:
            response = model.generate_content(request)
            if response:
                sleep(10)
                logging.info("AI analysis completed.")
                return response  # If successful, return the response
        except Exception as e:
            if '429' in str(e):
                logging.warning(f"Received 429 Too Many Requests. Retrying after {delay} seconds...")
                sleep(delay)
                delay += backoff_factor
                MODELS.append(model)  # Re-append the model if failed
            else:
                logging.error(f"Error occurred: {e}")
                raise

    logging.error("Max retries reached. Unable to complete the AI analysis.")
    return None


def text_processing(article_text):
    logging.info("Processing article text...")
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
    processed_article = ". ".join(sentences_list)
    return processed_article


def ai_analyzer(article, company_name):
    request = (f"I have several financial articles about {company_name}. I want you to analyze each one in turn "
               f"and provide the result in the form of: 3 sentences that best describe what the article is about, "
               f"and also I want you to provide a forecast based on this news, with what chance the stock price will "
               f"go up and with what chance it will go down in the format: '(decrease 30% | increase 70%)' - the total"
               f" should be 100%. And also how useful is this article for predicting the rise/fall of a stock in the "
               f"format '(Informativeness: 50%)'. Here is one of the articles: \n\n{article}")

    return request_processing(request).text


def get_rate(summary):
    logging.info("Extracting forecast and informativeness from AI summary...")

    forecast_pattern_1 = re.compile(r'\(decrease (\d+%) \| increase (\d+%)\)')
    forecast_pattern_2 = re.compile(r'\(increase (\d+%) \| decrease (\d+%)\)')
    informativeness_pattern = re.compile(r'\(informativeness: (\d+%)\)')

    lower_summary = summary.lower()
    forecasts = forecast_pattern_1.findall(lower_summary)
    if not forecasts:
        swap = forecast_pattern_2.findall(lower_summary)
        if swap:
            if len(swap[0]) >= 2:
                forecasts = [(swap[0][1], swap[0][0])]
        if not swap:
            forecasts = ["50%", "50%"]
    informativeness = informativeness_pattern.findall(lower_summary)
    if not informativeness:
        informativeness = 50
    else:
        informativeness = int(informativeness[0].replace('%', ''))

    decrease = int(forecasts[0][0].replace('%', ''))
    increase = int(forecasts[0][1].replace('%', ''))

    logging.info(f"Informativeness: {informativeness}, Decrease: {decrease}%, Increase: {increase}%")

    data = {
        'Decrease Probability': decrease,
        'Increase Probability': increase,
        'Informativeness': informativeness,
    }
    return data


def response_processing(response):
    logging.info("Processing AI response...")
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
