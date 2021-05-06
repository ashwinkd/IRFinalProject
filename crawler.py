import json
import logging
import pickle
import re
from urllib.parse import urljoin, urlparse

MAX_FILE_SIZE = 1024 * 1024
import hashlib
from urllib.request import urlopen

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)

IGNORED_EXTENSIONS = [
    # images
    '.mng', '.pct', '.bmp', '.gif', '.jpg', '.jpeg', '.png', '.pst', '.psp', '.tif',
    '.tiff', '.ai', '.drw', '.dxf', '.eps', '.ps', '.svg',

    # audio
    '.mp3', '.wma', '.ogg', '.wav', '.ra', '.aac', '.mid', '.au', '.aiff',

    # video
    '.3gp', '.asf', '.asx', '.avi', '.mov', '.mp4', '.mpg', '.qt', '.rm', '.swf', '.wmv',
    '.m4a',

    # other
    '.css', '.pdf', '.doc', '.exe', '.bin', '.rss', '.zip', '.rar',
]


class Crawler:
    link_graph = []
    visited_urls = set()
    url_to_content = {}
    url_to_body = {}
    filter_text = open('data_filter.txt', 'r').readlines()
    all_md5 = []

    def __init__(self, urls=[], max_pages=5000):
        self.all_urls = urls.copy()
        self.max_pages = max_pages
        self.urls_to_visit = urls

    def download_url(self, url):
        return requests.get(url).text

    def get_linked_urls(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            path = link.get('href')
            if path and path.startswith('/'):
                path = urljoin(url, path)
            domain = urlparse(path).netloc
            if not self.is_unique(path) or self.a_file(path) or "uic.edu" not in domain \
                    or path in self.visited_urls \
                    or path in self.urls_to_visit:
                self.visited_urls.add(path)
                continue
            self.add_content(path, url, link.contents)
            self.urls_to_visit.append(path)
            self.add_link(url, path)

    def crawl(self, url):
        html = self.download_url(url)
        self.visited_urls.add(url)
        # self.add_body(url, html)
        self.get_linked_urls(url, html)

    def add_content(self, url, parent, content):
        for c in content:
            if isinstance(c, str):
                c = self.clean_text(c.lower())
                if c:
                    if url not in self.url_to_content:
                        self.url_to_content[url] = {}
                    if parent not in self.url_to_content[url]:
                        self.url_to_content[url][parent] = set()
                    for ftext in self.filter_text:
                        ftext = self.clean_text(ftext)
                        if ftext not in c:
                            self.url_to_content[url][parent].add(c)

    def txt_md5(self, txt):
        txt = txt.encode('utf-8')
        return hashlib.md5(txt).hexdigest()

    def is_unique(self, url):
        try:
            c = urlopen(url)
            r = c.read(MAX_FILE_SIZE)
            soup = BeautifulSoup(r, features="lxml")
            header = soup.find('head').text
            body = soup.find('body').text
            md5 = [self.txt_md5(h) for h in [header, body]]
            if md5 not in self.all_md5:
                self.all_md5.append(md5)
                self.all_urls.append(url)
                return True
            else:
                return False
        except:
            return False

    @staticmethod
    def clean_text(text: str):
        text = re.sub(r"[^a-zA-Z ]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def add_body(self, url, html):
        url_text = set()
        soup = BeautifulSoup(html, 'html.parser')
        regex = re.compile('(title|description|text|quote|course)')
        htags = ["h1", "h2", "h3"]
        for tag in htags:
            for heading in soup.find_all(tag, {"class": regex}):
                heading = heading.getText()
                heading = self.clean_text(heading.lower())
                url_text.add(heading)
        for tag in ['div', 'section']:
            for EachPart in soup.find_all(tag, {"class": regex}):
                for text in EachPart.find_all(["h1", "h2", "h3", 'title', 'p']):
                    text = text.getText()
                    text = self.clean_text(text.lower())
                    url_text.add(text)
                text = EachPart.getText()
                text = self.clean_text(text.lower())
                url_text.add(text)

        for text in soup.find_all(['p']):
            text = text.getText()
            text = self.clean_text(text.lower())
            url_text.add(text)
        page_body = []
        for utext in url_text:
            addtext = True
            for ftext in self.filter_text:
                ftext = self.clean_text(ftext)
                if ftext in utext or utext in ftext:
                    if len(utext.split()) < 20:
                        addtext = False
                if ftext == utext or re.match(r'skip\sto\s.*content', utext):
                    addtext = False
            if addtext:
                page_body += [utext]
        self.url_to_body[url] = " . ".join(page_body)

    def get_data(self):
        data = {}
        for key in self.url_to_body:
            atext = ""
            if key in self.url_to_content:
                adict = self.url_to_content[key]
                asets = adict.values()
                aset = set()
                for elem in asets:
                    aset.update(elem)
                atext = " . ".join(list(aset))
            body = self.url_to_body[key]
            data[key] = {"atext": atext,
                         "body": body}
        for key in self.url_to_content:
            if key in self.url_to_body:
                continue
            adict = self.url_to_content[key]
            asets = adict.values()
            aset = set()
            for elem in asets:
                aset.update(elem)
            atext = " . ".join(list(aset))
            data[key] = {"atext": atext,
                         "body": ""}

        return data

    def run(self):
        urlnum = 0
        while urlnum < self.max_pages:
            if not self.urls_to_visit:
                break
            url = self.urls_to_visit.pop(0)
            logging.info(f'{urlnum}) Crawling: {url}')
            try:
                self.crawl(url)
                urlnum += 1
            except Exception:
                logging.exception(f'Failed to crawl: {url}')
        with open("data/data.json", "w") as outfile:
            json.dump(self.get_data(), outfile, indent=4)
            outfile.close()
        with open("data/link_graph2.pickle", "wb") as gfile:
            pickle.dump(self.link_graph, gfile)
            gfile.close()
        with open("all_links.pickle", "wb") as linkfile:
            pickle.dump(self.all_urls, linkfile)
            linkfile.close()

    def add_link(self, parent, child):
        parent_key = self.all_urls.index(parent)
        child_key = self.all_urls.index(child)
        if (parent_key, child_key) not in self.link_graph:
            self.link_graph.append((parent, child))

    def a_file(self, url):
        return url[-4:] in IGNORED_EXTENSIONS


def main():
    Crawler(urls=['https://cs.uic.edu/'], max_pages=100).run()


if __name__ == '__main__':
    main()
