#!/usr/bin/env python3

from email.utils import formatdate
import time
from operator import attrgetter

# RSS-reference → http://www.w3schools.com/rss/rss_reference.asp


class AtomFeed:
    def __init__(self, *args):
        self.channel = AtomChannel(*args)
        self.itemlist = []

    def addItem(self, *args):
        self.itemlist.append(AtomItem(*args))

    def sort_items_after_date(self):
        self.itemlist.sort(key=attrgetter("pubDate"), reverse=True)

    def getFeed(self):
        feed = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
"""
        feed += "\n<channel>\n"
        feed += self.channel.getInfo()

        for i in self.itemlist:
            feed += i.getItem()

        feed += "\n</channel>\n\n</rss>"

        return feed


class AtomBaseItem:
    def __init__(self, title, link, description):
        self.title = self.__escape_entities(title)
        self.link = self.__escape_entities(link)
        self.description = self.__escape_entities(description)

    def __escape_entities(self, text):
        """see http://www.w3.org/TR/REC-xml/#dt-chardata and
        http://www.w3.org/TR/REC-xml/#dt-escape"""
        text = text.replace("&", "&#38;")
        text = text.replace("<", "&#60;")
        text = text.replace(">", "&#62;")

        return text

    def getInfo(self):
        return """        <title>%s</title>
        <link>%s</link>
        <description>%s</description>""" % (
            self.title,
            self.link,
            self.description,
        )


class AtomChannel(AtomBaseItem):
    def __init__(self, title, link, description):
        super().__init__(title, link, description)
        self.url = link

    def getInfo(self):
        channel = (
            AtomBaseItem.getInfo(self)
            + """\n        <pubDate>%s</pubDate>\n
        <atom:link href="%s" rel="self" type="application/rss+xml"\
/> \n"""
            % (formatdate(localtime=True), self.url)
        )

        return channel


class AtomItem(AtomBaseItem):
    def __init__(self, title, link, description, pubDate=None, source=None):
        super().__init__(title, link, description)
        self.pubDate = pubDate
        self.__source = source

    def __get_pub_Date(self):
        if self.pubDate:
            return (
                "\n        <pubDate>"
                + formatdate(time.mktime(self.pubDate.timetuple()))
                + "</pubDate>"
            )
        else:
            return ""

    def __get_source(self):
        return ""
        pass  # TODO: <source> http://validator.w3.org/feed/docs/rss2.html#ltsourcegtSubelementOfLtitemgt or http://www.w3schools.com/RSS/rss_tag_source.asp

    #    if self.__source != None:
    #        return u"\n        <source>" + self.__source + "</source>"
    #    else:
    #        return u""

    def getItem(self):
        return """
    <item>
%s%s%s
    </item>""" % (
            self.getInfo(),
            self.__get_pub_Date(),
            self.__get_source(),
        )
