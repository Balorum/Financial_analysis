import re

text = "The new stocks that made the monthly cut could yield enormous returns in the coming years.\
Is BABA one of them?"


def text_preprocessor(text=text):
    pattern_1 = ("Is [A-Z]{1,20} one of them\W")
    text = re.sub(pattern_1, "1", text)
    text = text.lower()
    return text


print(text_preprocessor())

