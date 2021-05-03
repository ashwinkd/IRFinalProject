import json
import logging
import pickle
import re
from urllib.parse import urljoin, urlparse, urlsplit, urlunsplit, parse_qsl, urlencode, quote

import requests
from bs4 import BeautifulSoup
from url_normalize import url_normalize

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
    visited_urls = []
    url_to_content = {}
    url_to_body = {}
    filter_text = open('data_filter.txt', 'r').readlines()

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
            path = self.canonicalize(path)
            domain = urlparse(path).netloc
            if path and "uic.edu" in domain.lower():
                self.add_content(path, url, link.contents)
                if path not in self.visited_urls and path not in self.urls_to_visit:
                    if not self.a_file(path):
                        if path not in self.all_urls:
                            self.all_urls.append(path)
                        self.urls_to_visit.append(path)
                        self.add_link(url, path)
            else:
                self.visited_urls.append(path)

    def crawl(self, url):
        html = self.download_url(url)
        self.visited_urls.append(url)
        self.add_body(url, html)
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

    def canonicalize(self, url):
        split = urlsplit(url_normalize(url))
        path = quote(split[2])

        while path.startswith('/..'):
            path = path[3:]

        while path.endswith('%20'):
            path = path[:-3]

        qs = urlencode(sorted(parse_qsl(split.query)))
        return urlunsplit((split.scheme, split.netloc, path, qs, ''))

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
        with open("data.json", "w") as outfile:
            json.dump(self.get_data(), outfile, indent=4)
            outfile.close()
        with open("link_graph.pickle", "wb") as gfile:
            pickle.dump(self.link_graph, gfile)
            gfile.close()
        with open("all_links.pickle", "w") as linkfile:
            pickle.dump(self.all_urls, linkfile)
            linkfile.close()

    def add_link(self, parent, child):
        parent_key = self.all_urls.index(parent)
        child_key = self.all_urls.index(child)
        if (parent_key, child_key) not in self.link_graph:
            self.link_graph.append((parent_key, child_key))

    def a_file(self, url):
        return url[-4:] in IGNORED_EXTENSIONS


def main():
    Crawler(urls=['https://cs.uic.edu/']).run()


if __name__ == '__main__':
    main()
