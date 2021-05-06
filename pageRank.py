import pickle

import numpy as np


class TSPageRank:
    """
    This is an implementation of topic specific page rank
    """
    url_to_keys = pickle.load(open('data/url_keys.pickle', 'rb'))
    graph = pickle.load(open('data/link_graph.pickle', 'rb'))

    def __init__(self, num_iterations=20, alpha=0.2):
        self.num_iterations = num_iterations
        self.alpha = alpha

    def create_matrix(self, urls):
        M = np.empty(shape=[len(urls), len(urls)])
        keys = []
        for u in urls:
            if u not in self.url_to_keys:
                keys.append("NAN")
                continue
            key = self.url_to_keys[u]
            keys.append(key)
        for p, c in self.graph:
            if p not in keys or c not in keys:
                continue
            c = keys.index(c)
            p = keys.index(p)
            M.itemset((c, p), 1)
        for node in range(len(urls)):
            col = M[:, node]
            s = np.sum(col)
            if s > 0:
                col /= s
            M[:, node] = col
        return M

    def get_pageranks(self, urls_to_scores):
        urls = list(urls_to_scores.keys())
        M = self.create_matrix(urls)
        v = [1 / len(urls_to_scores) for _ in urls_to_scores]
        p_hat = np.array(list(urls_to_scores.values()))
        for _ in range(self.num_iterations):
            # print(v)
            v2 = M.dot(v)
            v2 = (1 - self.alpha) * v2
            v = v2 + p_hat
        pgscores = list(zip(urls, v))
        return sorted(pgscores, key=lambda x: x[1], reverse=True)
