#!/usr/bin/env python
# -*- coding: utf-8 -*-

from copy import deepcopy
from datetime import datetime
import locale
import urllib2
from urlparse import urljoin
from os import path

from HTMLParser import HTMLParser

class GenericParser(HTMLParser):
    '''Basic tools to collect information from a single webpage (→ self._url)'''
    def __init__(self, url):
        HTMLParser.__init__(self)
        self._url = url

        self.__template_item_info = { "title" : u"",
                                      "link" : None,
                                      "description" : u"",
                                      "source" : self._url,
                                      "pubDate" : None,
                                     }
        self._list_url_info = []

        self._act_info = deepcopy(self.__template_item_info)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def _attrs_to_dict(self, attrs_list):
        """Converts HTMLParser's attrs list to an dict. Thus, a check,
        whether a attribute exists, is simplified via has_key()"""
        attrs_dict = {}

        for key, value in attrs_list:
            attrs_dict[key] = value

        return attrs_dict

    def _download_page(self):
        request = urllib2.Request(self._url, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en'})
        response = urllib2.urlopen(request).read()
        return unicode(response, "utf-8")

    def _parse_URLs(self):
        try:
            self.feed(self._download_page())
        except urllib2.HTTPError as error:
            print error, "on", self._url

    def _next_url_info(self):
        self._list_url_info.append(deepcopy(self._act_info))
        self._act_info = deepcopy(self.__template_item_info)

    def rm_whitespace(self, string_whitespace):
        return " ".join(string_whitespace.split())

    def getData(self):
        return self._list_url_info

    def handle_starttag(self, tag, attrs):
        pass

    def handle_data(self, data):
        pass

    def handle_endtag(self, tag):
        pass


class SoundcloudDescriptionParser(GenericParser):
    def __init__(self, url):
        GenericParser.__init__(self, url)

        self._inside_article = False
        self._description_text = u""

        self._parse_URLs()

    def getData(self):
        return self._description_text

    def handle_starttag(self, tag, attrs):
        if tag == "article":
            self._inside_article = True
            return

        if tag == "meta" and self._inside_article:
            attrs = self._attrs_to_dict(attrs)
            if attrs.has_key("itemprop") and attrs["itemprop"] == "description" and attrs.has_key("content"):
                self._description_text = attrs["content"]

    def handle_endtag(self, tag):
        if tag == "article" and self._inside_article:
            self._inside_article = False


class SoundcloudParser(GenericParser):
    def __init__(self, url):
        GenericParser.__init__(self, url)

        self._found_track = False

        self._collect_pubdate = False
        self._pubdate_string = u""

        self._collect_title = False
        self._title_string = u""

        self._parse_URLs()

        for elem in self._list_url_info:
            parser = SoundcloudDescriptionParser(elem["link"])
            elem["description"] = parser.getData()

    def __unicode__(self):
        return u"Soundcloud"

    def _next_url_info(self):
        GenericParser._next_url_info(self)

        self._pubdate_string = u""
        self._title_string = u""

    def handle_starttag(self, tag, attrs):
        attrs = self._attrs_to_dict(attrs)

        if tag == "article" and attrs.has_key("class")\
           and attrs["class"] == "audible":
            self._found_track = True

        if self._found_track:
            if tag == "a" and attrs.has_key("itemprop") and\
               attrs["itemprop"] == "url":
                    self._act_info["link"] = urljoin(self._url, attrs["href"])
                    self._collect_title = True

            if tag == "time" and attrs.has_key("pubdate"):
                self._collect_pubdate = True

    def handle_data(self, data):
        if self._collect_pubdate:
            self._pubdate_string += data

        if self._collect_title:
            self._title_string += data

    def handle_endtag(self, tag):
        if tag == "article" and self._found_track:
            self._found_track = False
            self._next_url_info()

        if tag == "a" and self._collect_title:
            self._act_info["title"] = self.rm_whitespace(self._title_string)
            self._collect_title = False

        if tag == "time" and self._collect_pubdate:
            self._collect_pubdate = False

            # TODO: datetime.strptime doesnt support %z in python 2.x
            # see http://bugs.python.org/issue6641
            # → trace +0000
            self._act_info["pubDate"] = datetime.strptime(self._pubdate_string[:-6],
                                                   "%Y/%m/%d  %H:%M:%S")


class TwitterParser(GenericParser):
    def __init__(self, url):
        GenericParser.__init__(self, url)

        self.__found_description = False

        self.__found_twitter_username = False
        self.__twitter_username = u""

        self.__html_encoding = u""

        self._parse_URLs()

    def __unicode__(self):
        return u"Twitter"

    def handle_starttag(self, tag, attrs):
        attrs = self._attrs_to_dict(attrs)

        # get encoding of HTML-document
        if tag == "meta" and attrs.has_key("charset"):
            self.__html_encoding = attrs["charset"]

        # search username
        if tag == "a" and attrs.has_key("class"):
            if "ProfileHeaderCard-nameLink" in attrs["class"]:
                self.__found_twitter_username = True

        # search link and pubDate
        if (tag == "a" and attrs.has_key("title") and
             attrs.has_key("href") and attrs.has_key("class")):
            if "tweet-timestamp" in attrs["class"]:
                self._act_info["link"] = "https://twitter.com" + attrs["href"]

                date_string = attrs["title"].encode(self.__html_encoding)

                # example format: '2:07 PM - 3 Oct 2014'
                self._act_info["pubDate"] = datetime.strptime(date_string,
                                            "%I:%M %p - %d %b %Y")

                # create title after required data (username and pubDate)
                # are collected
                self._act_info["title"] = u"[" + self.__twitter_username +\
                                "] Tweet " +\
                                self._act_info["pubDate"].isoformat(" ")

        # search beginning of description
        if tag == "p" and attrs.has_key("class"):
            if "tweet-text" in attrs["class"]:
                self.__found_description = True

    def handle_data(self, data):
        if self.__found_twitter_username:
            self.__twitter_username += data

        if self.__found_description:
            self._act_info["description"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.__found_twitter_username:
            self.__found_twitter_username = False

        if tag == "p" and self.__found_description:
            self.__found_description = False
            self.description_finished = True
            self._next_url_info()


if __name__ == "__main__":
    print "Small manual test"

    soundcloud = SoundcloudParser(u"https://soundcloud.com/soundcloud")
    soundcloud_test = soundcloud.getData()

    '''
    print "######################################"
    s = SoundcloudParser("")
    s.feed("""
    <article class="audible" itemprop="track" itemscope itemtype="http://schema.org/MusicRecording">
        <h1 itemprop="name">
            <a itemprop="url" href="/calvinharris/calvin-harris-blame-feat-john-newman-acapella">Calvin Harris - Blame feat John Newman Acapella</a>
        </h1>
        by <a href="/calvinharris">Calvinharris</a>
        published on <time pubdate>2015/03/17 02:27:34 +0000</time>
        <meta itemprop="duration" content="PT00H02M50S" />
    </article>
    """)
    print s.getData()

    print "######################################"
    s2 = SoundcloudParser("")
    s2.feed("""
    <article class="audible" itemprop="track" itemscope itemtype="http://schema.org/MusicRecording">
        <h1 itemprop="name">
            <a itemprop="url" href="/calvinharris/calvin-harris-blame-feat-john-newman-acapella">Calvin Harris - Blame feat John Newman Acapella</a>
        </h1>

        published on <time pubdate>2015/03/17 02:27:34 +0000</time>
        <meta itemprop="duration" content="PT00H02M50S" />
    </article>
    """)
    print s2.getData()
    '''
    twitter = TwitterParser(u"https://twitter.com/twitter")
    twitter_test = twitter.getData()

    for t in soundcloud_test, twitter_test:
        print "###########################################################"
        for i in t:
            print i["title"]
            print i["link"]
            print i["pubDate"]
            print i["description"]
            print "--------------------------------------------------------"
