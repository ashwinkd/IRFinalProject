# UIC Search Engine

### Read Report for detailed explanation:

[Report](https://github.com/ashwinkd/Search-Engine/blob/master/Search_Engine_for_UIC_Domain_Report.pdf)

### Screenshots:
Main Page:
<p align="center">
<img width="400" src="https://github.com/ashwinkd/IRFinalProject/blob/master/Screenshots/main_page.png">
</p>
Results Page:
<p align="center">
<img width="500" src="https://github.com/ashwinkd/IRFinalProject/blob/master/Screenshots/result_page.png">
</p>

### Follow these steps to run on your system
```
$ git clone https://github.com/ashwinkd/IRFinalProject.git
$ cd IRFinalProject
$ pip install -r requirements.txt
$ cd WebCrawl/spiders; scrapy crawl uic (optional)
$ python main.py
```


### Function of Each File:

* **crawler.py** 
    Starting with the seed: 'https://cs.uic.edu/' crawler parses indexes imformation and adds all href links in the page. This used BeautifulSoup library.<br>
    Output: *data.json* file
* **search_engine.py**
    Takes all crawled data in *data.json* outputs a BERT feature vector for each page. 
    Given a query returns a list of top 100 pages based on cosine simlarity. <br>
    Output: *document_embeddings.h5* file
* **main.py**
    This implements the GUI for the project. Contains two pages:
    * Main Page: Here you can enter your query
    * Result Page: Here you can see the results. By default shows top 10 results.
* **evaluate.py**
    This is a small script that runs a Spearman Ranked Correlation Coefficient and Recall Evaluation of 5 queries.
* **Search-Engine/WebCrawl/spiders/uic_spyder.py**
    This is the Scrapy crawler which fetches page data and web-graph for PageRank Algorithm.  <br>
* **pageRank.py**
    This implements the PageRank algorithm specified in the Report.

### Data Folder:

* **data.pickle**: Contains Title, URL, Boddy and atag Text.
* **results.json**: Containsgold-standard results for evaluation.
* **link_graph.pickle**: Consist of a list of parent to child href links
* **tfidf_data.pickle**: Consists of term freq, inverse document frequence and document length
* **bert_embeddings.h5**: Contains the documents embeddings of shape (7640 x 768).
    
    
