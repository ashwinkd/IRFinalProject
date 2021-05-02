import json
import re

import h5py
from scipy.spatial.distance import cdist
from sentence_transformers import SentenceTransformer


class SearchEngine:
    model = SentenceTransformer('bert-base-nli-mean-tokens')
    document_embeddings = None
    embeddings_file = "document_embeddings.h5"

    def __init__(self, fresh_start=False):
        self.documents = []
        self.urls = []
        self.import_data()
        self.create_model(fresh_start)

    def import_data(self):
        data = json.load(open('data.json'))
        for url, text_dict in data.items():
            self.urls.append(url)
            document = text_dict['atext']
            self.documents.append(document)

    def create_model(self, fresh_start):
        if fresh_start:
            self.create_embeddings()
        else:
            self.read_embeddings()

    def search(self, query):
        qresults = []
        if not query or not isinstance(query, str):
            return qresults
        query = self.clean_text(query)
        queries = [query]
        query_embeddings = self.model.encode(queries)
        for query, query_embedding in zip(queries, query_embeddings):
            distances = cdist([query_embedding], self.document_embeddings, "cosine")[0]
            results = zip(range(len(distances)), distances)
            results = sorted(results, key=lambda x: x[1])
            if len(results) > 100:
                results = results[:100]
            for idx, distance in results:
                print(self.documents[idx].strip(), "(Cosine Score: %.4f)" % (1 - distance))
                qresults.append((self.documents[idx], self.urls[idx]))
        return qresults

    def clean_text(self, query):
        query = query.lower()
        query = re.sub(r'[^a-zA-Z0-9 ]', ' ', query)
        query = re.sub(r'\s+', ' ', query).strip()
        return query

    def read_embeddings(self):
        h5f = h5py.File(self.embeddings_file, 'r')
        self.document_embeddings = h5f['dataset_1'][:]

    def create_embeddings(self):
        self.document_embeddings = self.model.encode(self.documents)
        h5f = h5py.File(self.embeddings_file, 'w')
        h5f.create_dataset('dataset_1', data=self.document_embeddings)
        h5f.close()


def main():
    # return
    se = SearchEngine(fresh_start=True)
    results = se.search("Undergraduate courses")
    print(results)


if __name__ == '__main__':
    main()
