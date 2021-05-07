import json

from scipy.stats import spearmanr

from search_engine import SearchEngine

results = json.load(open('data/results.json'))
se = SearchEngine(fresh_start=False)
for query, target in results.items():
    pred = se.search(query)
    pred = [x[1] for x in pred[:10]]
    rho = spearmanr(pred, target)
    print(rho.correlation, rho.pvalue)
