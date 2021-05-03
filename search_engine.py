import json
import re

import h5py
from scipy.spatial.distance import cdist
from sentence_transformers import SentenceTransformer

from pageRank import TSPageRank
from preprocessor import Preprocessor


class SearchEngine:
    model = SentenceTransformer('bert-base-nli-mean-tokens')
    document_embeddings_field1 = None
    document_embeddings_field2 = None
    preprocessor = Preprocessor(stemmer_flag=True, stopwords_flag=True, min_word_length=2)
    embeddings_file1 = "bert_embeddings_f1.h5"
    embeddings_file2 = "bert_embeddings_f2.h5"
    pagerank = TSPageRank()

    @staticmethod
    def clean_text(text: str):
        text = re.sub(r"[^a-zA-Z ]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def __init__(self, fresh_start=False):
        self.documents_field1 = []
        self.documents_field2 = []
        self.urls = []
        self.import_data()
        self.create_model(fresh_start)

    def import_data(self):
        data = json.load(open('data.json'))
        for url, text_dict in data.items():
            self.urls.append(url)
            document1 = text_dict['atext']
            self.documents_field1.append(document1)
            document2 = text_dict['body']
            self.documents_field2.append(document2)

    def create_model(self, fresh_start):
        if fresh_start:
            self.create_embeddings()
        else:
            self.read_embeddings()

    def search(self, query):
        qresults = []
        if not query or not isinstance(query, str):
            return qresults
        query = SearchEngine.clean_text(query.lower())
        queries = [query]
        query_embeddings = self.model.encode(queries)
        for query, query_embedding in zip(queries, query_embeddings):
            distances1 = cdist([query_embedding], self.document_embeddings_field1, "cosine")[0]
            distances2 = cdist([query_embedding], self.document_embeddings_field2, "cosine")[0]

            results1 = list(zip(range(len(distances1)), distances1))
            results2 = list(zip(range(len(distances2)), distances2))

            results = self.get_average_rank(results1, results2, weights=[0.8, 0.2])

            if len(results) > 100:
                results = results[:100]

            for idx, distance in results:
                print(self.documents_field1[idx].strip(), "(Cosine Score: %.4f)" % (1 - distance))
                qresults.append((self.documents_field1[idx], self.urls[idx]))
        return qresults

    def clean_text(self, query):
        query = query.lower()
        query = re.sub(r'[^a-zA-Z0-9 ]', ' ', query)
        query = re.sub(r'\s+', ' ', query).strip()
        return query

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
            results.append((ri, weights[0] * results1[ri] + weights[1] * results2[ri]))
        results = sorted(results, key=lambda x: x[1])
        s = sum(x[1] for x in results)
        results = [(self.urls[x[0]], x[1] / s) for x in results]
        urls_to_cores = dict(zip(*results))
        pgscores = self.pagerank.get_pageranks(urls_to_cores)
        pgscores = [(self.urls.index(url), score) for url, score in pgscores]
        return pgscores


def main():
    # return
    se = SearchEngine(fresh_start=True)
    results = se.search("Undergraduate courses")
    print(results)


if __name__ == '__main__':
    main()
