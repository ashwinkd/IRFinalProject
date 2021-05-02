## Ashwin Deshpande - 655640269
import re
import string

from nltk.stem import PorterStemmer


class Preprocessor:
    def __init__(self, stemmer_flag: bool, stopwords_flag: bool, min_word_length: int):
        self.stopwords_flag = stopwords_flag
        self.porter_stemmer = PorterStemmer()
        self.stemmer_flag = stemmer_flag
        self.min_word_length = min_word_length
        self.stopwords = self.read_stopwords_list()

    def read_stopwords_list(self):
        '''
        Import a list of stopwords from stopwords.txt
        :return:
        '''
        stopword_fptr = open('./stopwords.txt')
        stopwords = stopword_fptr.read()
        stopwords = set(stopwords.split())
        return stopwords

    def preprocess(self, text):
        '''
        Performs following tasks
        * Removes punctuation given in string.punctuation
        * Splits text into a list of word tokens
        * Removes stopwords from list of word tokens if specified
        * Stems word in list of word tokens if specified
        :param text:
        :return:
        '''
        text_tokens = []
        text = self.convert_to_lower_case(text)
        text = self.remove_punctuation(text)
        text = self.remove_numbers(text)
        for token in self.tokenize(text):
            if self.stemmer_flag:
                token = self.stem(token)
            if len(token) <= self.min_word_length:
                continue
            if self.stopwords_flag and self.is_stop_word(token):
                continue
            text_tokens.append(token)
        return " ".join(text_tokens)

    def remove_punctuation(self, text):
        """
        Replace punctuation characters with whitespace
        :param text:
        :return:
        """
        text = re.sub(r'[' + string.punctuation + ']', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def tokenize(self, text):
        """
        Split on whitespace
        :param text:
        :return:
        """
        text = text.split()
        return text

    def is_stop_word(self, word):
        """
        true if word is stop word, false if not
        :param word:
        :return:
        """
        return word in self.stopwords

    def stem(self, word):
        """
        Using Porter Stemmer stem word
        :param word:
        :return:
        """
        return self.porter_stemmer.stem(word)

    def convert_to_lower_case(self, text):
        return text.lower()

    def remove_numbers(self, text):
        """
        Replace number characters with whitespace
        :param text:
        :return:
        """
        text = re.sub(r'[0-9]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
