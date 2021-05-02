# UIC Search Engine

### Screenshots:

<img src="https://github.com/ashwinkd/IRFinalProject/blob/master/Screenshots/main_page.png" alt="Main Page" width="400"/>  <img src="https://github.com/ashwinkd/IRFinalProject/blob/master/Screenshots/result_page.png" alt="Result Page" width="500"/>


### Follow these steps to run on your system
```
$ git clone https://github.com/ashwinkd/IRFinalProject.git
$ cd IRFinalProject
$ pip install -r requirements.txt
$ python crawler.py
$ python main.py
```


### Function of Each File

* **crawler.py** 
    Starting with the seed: 'https://cs.uic.edu/' crawler parses indexes imformation and adds all href links in the page.<br>
    Output: *data.json* file
* **search_engine.py**
    Takes all crawled data in *data.json* outputs a BERT feature vector for each page. 
    Given a query returns a list of top 100 pages based on cosine simlarity. <br>
    Output: *document_embeddings.h5* file
* **main.py**
    This implements the GUI for the project. Contains two pages:
    * Main Page: Here you can enter your query
    * Result Page: Here you can see the results. By default shows top 10 results.
    
