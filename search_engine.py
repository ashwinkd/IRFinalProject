import pickle
import re
from math import log

import h5py
import nltk
from nltk.tokenize import word_tokenize
from scipy.spatial.distance import cdist
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer

from pageRank import TSPageRank
from preprocessor import Preprocessor

nltk.download('punkt')


class SearchEngine:
    model = SentenceTransformer('bert-base-nli-mean-tokens')
    vectorizer = TfidfVectorizer()
    document_embeddings_field1 = None
    document_embeddings_field2 = None
    preprocessor = Preprocessor(stemmer_flag=True, stopwords_flag=True, min_word_length=2)

    pagerank = TSPageRank()

    def clean_text(self, text: str):
        text = re.sub(r"[^a-zA-Z ]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def __init__(self, method, fresh_start=False):
        self.document_lengths = {}
        self.method = method
        self.embeddings_file1 = f"data/bert_embeddings_f1.h5"
        self.embeddings_file2 = f"data/bert_embeddings_f2.h5"
        self.documents_field1 = []
        self.documents_field2 = []
        self.document_titles = {}
        self.urls = []
        self.tf = {}
        self.idf = {}
        self.import_data(fresh_start)
        self.create_model(fresh_start)

    def import_data(self, fresh_start):
        data = pickle.load(open('data/data.pickle', 'rb'))
        for url, text_dict in data.items():
            self.urls.append(url)
            document1 = text_dict['atext']
            self.documents_field1.append(self.clean_text(document1))
            document2 = text_dict['body']
            self.documents_field2.append(self.clean_text(document2))
            if 'title' in text_dict:
                title = text_dict['title']
                self.document_titles[url] = title
            if fresh_start:
                self.add_to_index("{} {}".format(document1, document2), url)
        if fresh_start:
            self.add_idf(N=len(data))
            with open('data/tfidf_data.pickle', 'wb') as fptr:
                pickle.dump([self.tf, self.idf, self.document_lengths], fptr)
        else:
            with open('data/tfidf_data.pickle', 'rb') as fptr:
                self.tf, self.idf, self.document_lengths = pickle.load(fptr)

    def create_model(self, fresh_start):
        if self.method == "TFIDF":
            return
        if fresh_start:
            self.create_embeddings()
        else:
            self.read_embeddings()

    def search(self, query):
        qresults = []
        results = []
        if not query or not isinstance(query, str):
            return qresults
        if self.method == "BERT":
            query = self.clean_text(query.lower())
            queries = [query]
            query_embeddings = self.model.encode(queries)
            for query, query_embedding in zip(queries, query_embeddings):
                distances1 = cdist([query_embedding], self.document_embeddings_field1, "cosine")[0]
                distances2 = cdist([query_embedding], self.document_embeddings_field2, "cosine")[0]

                results1 = list(zip(range(len(distances1)), distances1))
                results2 = list(zip(range(len(distances2)), distances2))

                results = self.get_average_rank(results1, results2, weights=[0.8, 0.2])
        elif self.method == "TFIDF":
            qwords = word_tokenize(query.lower())
            results = self.get_cosine(qwords)

        if len(results) > 100:
            results = results[:100]

        for url, score in results:
            title = self.document_titles[url]
            qresults.append((title, url))

        return qresults

    def get_cosine(self, query_tokens):
        query_length = 0
        scores = {}
        for token in set(query_tokens):
            if token not in self.tf:
                continue
            qtoken_tf = query_tokens.count(token)
            idf = self.idf[token]
            qtoken_tfidf = qtoken_tf * idf
            query_length += qtoken_tfidf ** 2
            for doc_id, dtoken_tfidf in self.tf[token].items():
                if doc_id not in scores:
                    scores[doc_id] = 0
                scores[doc_id] += qtoken_tfidf * dtoken_tfidf
        scores = self.normalize_score(scores, query_length)
        scores = sorted(scores, key=lambda x: x[1], reverse=True)
        return scores

    def normalize_score(self, scores, query_length):
        normalized_scores = []
        for doc_id, score in scores.items():
            doc_length = self.document_lengths[doc_id]
            score = score / ((query_length * doc_length) ** (1 / 2))
            normalized_scores.append((doc_id, score))
        return normalized_scores

    def clean_text(self, text):
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9 ]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def read_embeddings(self):
        h5f1 = h5py.File(self.embeddings_file1, 'r')
        self.document_embeddings_field1 = h5f1['dataset_1'][:]
        h5f1.close()
        h5f2 = h5py.File(self.embeddings_file2, 'r')
        self.document_embeddings_field2 = h5f2['dataset_1'][:]
        h5f2.close()

    def create_embeddings(self):
        self.document_embeddings_field1 = self.model.encode(self.documents_field1)
        h5f1 = h5py.File(self.embeddings_file1, 'w')
        h5f1.create_dataset('dataset_1', data=self.document_embeddings_field1)
        h5f1.close()

        self.document_embeddings_field2 = self.model.encode(self.documents_field2)
        h5f2 = h5py.File(self.embeddings_file2, 'w')
        h5f2.create_dataset('dataset_1', data=self.document_embeddings_field2)
        h5f2.close()

    def get_average_rank(self, results1, results2, weights):
        results = []
        for ri in range(len(results1)):
            score1 = results1[ri][1]
            score2 = results2[ri][1]
            results.append((ri, weights[0] * score1 + weights[1] * score2))
        results = sorted(results, key=lambda x: x[1], reverse=True)
        s = sum(x[1] for x in results)
        results = {self.urls[x[0]]: x[1] / s for x in results}
        pgscores = self.pagerank.get_pageranks(results)
        pgscores = [(url, score) for url, score in pgscores]
        return pgscores

    def add_to_index(self, text, url):
        words = word_tokenize(text)
        for w in words:
            if w not in self.tf:
                self.tf[w] = {}
            if url not in self.tf[w]:
                self.tf[w][url] = 0
            self.tf[w][url] += 1

    def add_idf(self, N):
        for w, doc in self.tf.items():
            idf = log(N / len(doc))
            self.idf[w] = idf
            for url, tf in doc.items():
                tfidf = tf * idf
                self.tf[w][url] = tfidf
                if url not in self.document_lengths:
                    self.document_lengths[url] = 0
                self.document_lengths[url] += tfidf ** 2


def main():
    se = SearchEngine(fresh_start=False, method='TFIDF')
    results = se.search("Undergraduate courses")
    print(results)


if __name__ == '__main__':
    main()
