import collections
import hashlib
import pickle
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from scrapy.exceptions import CloseSpider
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from tld import get_tld
from w3lib.url import canonicalize_url

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


class UICSpyder(CrawlSpider):
    crawled = 0
    url_to_md5 = {}
    all_urls = list()
    filter_text = open('data_filter.txt', 'r').readlines()
    url_to_content = {}
    url_to_title = {}
    url_to_body = {}
    link_graph = []
    N = 1000
    count = 0
    name = "uic"
    visited_urls = set()
    start_urls = ["https://cs.uic.edu/"]
    rules = (Rule(LinkExtractor(allow_domains='uic.edu',
                                canonicalize=True,
                                unique=True),
                  callback='parse_item',
                  follow=True),)

    def parse_item(self, response):
        url = response.request.url
        html = requests.get(url).text
        print(f"Crawling {self.count}: {url}")
        self.visited_urls.add(url)
        if self.count >= self.N:
            raise CloseSpider(f"Crawled {self.count} pages. Exiting.")
        self.count += 1
        self.url_to_md5[url] = self.txt_md5(url)
        self.url_to_title[url] = self.get_title(url)
        self.add_body(url, html)
        self.get_linked_urls(url, html)
        print("*" * 30)
        if len(self.url_to_content) > self.crawled + 100:
            self.crawled = len(self.url_to_content)
            self.save_data()

    def get_linked_urls(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            path = link.get('href')
            if path and path.startswith('/'):
                path = urljoin(url, path)
            try:
                path = canonicalize_url(path)
                res = get_tld(path, as_object=True)
                domain = res.fld
            except:
                continue
            if self.a_file(path) or "uic.edu" not in domain:
                continue
            self.add_content(path, link.getText())
            self.add_link(url, path)

    def add_body(self, url, html):
        url_text = set()
        soup = BeautifulSoup(html, 'html.parser')
        regex = re.compile('(title|description|text|quote|course|intro|content)')
        htags = ["h1", "h2", "h3"]
        for tag in htags:
            for heading in soup.find_all(tag, {"class": regex}):
                heading = heading.getText()
                heading = self.clean_text(heading.lower())
                url_text.add(heading)
        for tag in ['div', 'section', 'span']:
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

    def add_link(self, parent, child):
        if parent in self.url_to_md5:
            parent_key = self.url_to_md5[parent]
        else:
            parent_key = self.txt_md5(parent)
            self.url_to_md5[parent] = parent_key
        if child in self.url_to_md5:
            child_key = self.url_to_md5[child]
        else:
            child_key = self.txt_md5(child)
            self.url_to_md5[child] = child_key
        if (parent_key, child_key) not in self.link_graph:
            self.link_graph.append((parent_key, child_key))

    def txt_md5(self, txt):
        txt = txt.encode('utf-8')
        return hashlib.md5(txt).hexdigest()

    def a_file(self, url):
        return url[-4:] in IGNORED_EXTENSIONS

    def add_content(self, url, content):
        if not isinstance(content, str):
            return
        content = self.clean_text(content.lower())
        if not content:
            return
        if url not in self.url_to_content:
            self.url_to_content[url] = set()
        if content in self.url_to_content[url]:
            return
        addtext = True
        for ftext in self.filter_text:
            ftext = self.clean_text(ftext)
            if ftext in content or content in ftext:
                addtext = False
        if not addtext:
            return
        if url not in self.url_to_title:
            self.url_to_title[url] = self.get_title(url)
        self.url_to_content[url].add(content)

    def clean_text(self, text: str):
        text = re.sub(r"[^a-zA-Z0-9 -,.&\"%$@()]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def get_data(self):
        data = {}
        keys = list(self.url_to_content.keys()) + list(self.url_to_body.keys())
        for key in keys:
            atext = ""
            if key in self.url_to_content:
                aset = self.url_to_content[key]
                atext = " . ".join(list(aset))
            body = ""
            if key in self.url_to_body:
                body = self.url_to_body[key]
            title = ""
            if key in self.url_to_title:
                title = self.url_to_title[key]
            data[key] = {"atext": atext,
                         "body": body,
                         "title": title}
        return collections.OrderedDict(data)

    def save_data(self):
        with open('../../data/link_graph.pickle', 'wb') as fptr:
            pickle.dump(self.link_graph, fptr)
            fptr.close()
        with open('../../data/data.pickle', 'wb') as fptr:
            pickle.dump(self.get_data(), fptr)
            fptr.close()
        with open('../../data/url_keys.pickle', 'wb') as fptr:
            pickle.dump(collections.OrderedDict(self.url_to_md5), fptr)
            fptr.close()

    def get_title(self, url):
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        title = str(soup.title.string)
        title = re.sub("\s+", " ", title).strip()
        return title
