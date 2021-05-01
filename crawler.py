import json
import logging
import re
from urllib.parse import urljoin, urlparse, urlsplit, urlunsplit, parse_qsl, urlencode, quote

import requests
from bs4 import BeautifulSoup
from url_normalize import url_normalize

logging.basicConfig(
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)


class Crawler:

    def __init__(self, urls=[], max_pages=3500):

        self.max_pages = max_pages
        self.visited_urls = []
        self.url_to_content = {}
        self.url_to_body = {}
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
                    self.add_url_to_visit(path)

    def add_url_to_visit(self, url):
        self.urls_to_visit.append(url)

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

    def clean_text(self, text):
        text = re.sub(r"[^a-zA-Z ]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def add_body(self, url, html):
        url_text = set()
        soup = BeautifulSoup(html, 'html.parser')
        regex = re.compile('(^|[^a-zA-Z])(title|description|text)([^a-zA-Z]|$)')
        htags = ["h1", "h2", "h3"]
        for tag in htags:
            for heading in soup.find_all(tag, {"class": regex}):
                heading = heading.getText()
                heading = self.clean_text(heading.lower())
                url_text.add(heading)
        for tag in ['div', 'section']:
            for EachPart in soup.find_all(tag, {"class": regex}):
                for heading in EachPart.find_all(["h1", "h2", "h3"]):
                    heading = heading.getText()
                    heading = self.clean_text(heading.lower())
                    url_text.add(heading)
                for title in EachPart.find_all('title'):
                    title = title.getText()
                    title = self.clean_text(title.lower())
                    url_text.add(title)
        for text in soup.find_all(['title', 'p']):
            text = text.getText()
            text = self.clean_text(text.lower())
            url_text.add(text)
        url_text = " . ".join(url_text)
        self.url_to_body[url] = url_text

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


def main():
    Crawler(urls=['https://cs.uic.edu/']).run()


if __name__ == '__main__':
    main()
