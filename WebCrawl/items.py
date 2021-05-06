# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class WebsearchItem(scrapy.Item):
    origin_link = scrapy.Field()
    title = scrapy.Field()
    contents = scrapy.Field()
    outlinks = scrapy.Field()
