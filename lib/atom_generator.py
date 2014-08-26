#!/usr/bin/env python
# -*- coding: utf-8 -*-

from email.Utils import formatdate
import time
from operator import attrgetter

## RSS-reference → http://www.w3schools.com/rss/rss_reference.asp

class AtomFeed(object):
    def __init__(self, *args):
        self.channel = AtomChannel(*args)
        self.itemlist = []
    
    def addItem(self, *args):
        self.itemlist.append(AtomItem(*args))
        
    def sort_items_after_date(self):
        self.itemlist.sort(key=attrgetter('pubDate'), reverse=True)
        
    def getFeed(self):
        feed = u"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
"""
        feed += u"\n<channel>\n"
        feed += self.channel.getInfo()
        
        for i in self.itemlist:
            feed += i.getItem()
        
        feed += u"\n</channel>\n\n</rss>"
        
        return feed
    
    
class AtomBaseItem(object):
    def __init__(self, title, link, description):
        self.title = self.__escape_entities(title)
        self.link = self.__escape_entities(link)
        self.description = self.__escape_entities(description)
        
    def __escape_entities(self, text):
        '''see http://www.w3.org/TR/REC-xml/#dt-chardata and
        http://www.w3.org/TR/REC-xml/#dt-escape'''
        text = text.replace(u"&", u"&#38;")
        text = text.replace(u"<", u"&#60;")
        text = text.replace(u">", u"&#62;")
        
        return text
    
    def getInfo(self):
        return u"""        <title>%s</title>
        <link>%s</link>
        <description>%s</description>""" %(self.title, self.link,
                                           self.description)
    
    
class AtomChannel(AtomBaseItem):
    def __init__(self, title, link, description):
        AtomBaseItem.__init__(self, title, link, description)
        self.url = link
        
    def getInfo(self):
        channel = AtomBaseItem.getInfo(self) +\
                u'''\n        <pubDate>%s</pubDate>\n
        <atom:link href="%s" rel="self" type="application/rss+xml"\
/> \n''' % (formatdate(localtime=True), self.url)
        
        return channel
    
    
class AtomItem(AtomBaseItem):
    def __init__(self, title, link, description, pubDate=None,
                    source=None):
        AtomBaseItem.__init__(self, title, link, description)
        self.pubDate = pubDate
        self.__source = source
        
    def __get_pub_Date(self):
        if self.pubDate != None:
            return u"\n        <pubDate>" +\
                    formatdate(time.mktime(self.pubDate.timetuple()))+\
                    "</pubDate>"
        else:
            return u""
        
    def __get_source(self):
        return u""
        pass # TODO: <source> http://validator.w3.org/feed/docs/rss2.html#ltsourcegtSubelementOfLtitemgt or http://www.w3schools.com/RSS/rss_tag_source.asp
    #    if self.__source != None:
    #        return u"\n        <source>" + self.__source + "</source>"
    #    else:
    #        return u""
            
    def getItem(self):
        return u"""
    <item>
%s%s%s
    </item>""" %( self.getInfo(), self.__get_pub_Date(),
                    self.__get_source() )
    
    
if __name__ == "__main__":   
    feed = AtomFeed(u"Test", u"http://exmaple.org",
                    u"Just for test purposes")
    
    for i in range(0,2):
        title = u"Testarticle %s" %i
        feed.addItem(title, u"http://example.org/article",
                     u"Article description should normally be here!")
    
    for i in range(0,2):
        title = u"Testarticle with source and pubDate %s" %i
        feed.addItem(title, u"http://example.org/article",
                     u"Article description should normally be here!", 
                     formatdate(), 
                     u"http://example.org/list-articles")
    print feed.getFeed()
