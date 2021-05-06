import pickle

import numpy as np


class TSPageRank:
    """
    This is an implementation of topic specific page rank
    """
    all_urls = list(pickle.load(open('data/url_keys.pickle', 'rb')).keys())
    all_keys = list(pickle.load(open('data/url_keys.pickle', 'rb')).values())
    graph = pickle.load(open('data/link_graph.pickle', 'rb'))
    # v = np.array([1 / len(all_urls) for node in all_urls])
    v = np.full(len(all_urls), 1 / len(all_urls))
    M = np.zeros(shape=[len(all_urls), len(all_urls)])

    def __init__(self, num_iterations=20, alpha=0.2):
        self.num_iterations = num_iterations
        self.alpha = alpha
        self.create_matrix()

    def create_matrix(self):
        for p, c in self.graph:
            c = self.all_keys.index(c)
            p = self.all_keys.index(p)
            self.M.itemset((c, p), 1)
        for node in range(len(self.all_urls)):
            col = self.M[:, node]
            s = np.sum(col)
            if s > 0:
                col /= s
            self.M[:, node] = col

    def get_pageranks(self, urls_to_cores):
        pgscores = []
        v = self.v.copy()
        p_hat = self.alpha * np.array([urls_to_cores[u] if u in urls_to_cores else 0 for u in self.all_urls])
        for _ in range(self.num_iterations):
            # print(v)
            v2 = self.M.dot(v)
            v2 = (1 - self.alpha) * v2
            v = v2 + p_hat
        for u in urls_to_cores:
            if u in self.all_urls:
                idx = self.all_urls.index(u)
                pgscores.append((u, v[idx]))
            else:
                print(u)
        return sorted(pgscores, key=lambda x: x[1])
