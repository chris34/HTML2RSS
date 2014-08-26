#!/usr/bin/env python
# -*- coding: utf-8 -*-

from copy import deepcopy
from datetime import datetime
import locale
from os import path
import urllib2

from HTMLParser import HTMLParser

class GenericParser(HTMLParser):
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
        
        self._attrs_dict = {}
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def _convert_attrs_list_to_dict(self, attrs_list):
        for key, value in attrs_list:
            self._attrs_dict[key] = value
    
    def _download_page(self):
        response = urllib2.urlopen(self._url).read()
        return unicode(response, "utf-8")
        
    def _parse_URLs(self):
        try:
            self.feed(self._download_page())
        except urllib2.HTTPError as error:
            print error, "on", self._url
        
    def _next_url_info(self):
        self._list_url_info.append(deepcopy(self._act_info))
        self._act_info = deepcopy(self.__template_item_info)
        
    def getData(self):
        return self._list_url_info
    
    def handle_starttag(self, tag, attrs):
        pass
        
    def handle_data(self, data):
        pass
        
    def handle_endtag(self, tag):
        pass
    
    
class SoundcloudParser(GenericParser):
    def __init__(self, url):
        GenericParser.__init__(self, url)
        
        self.track_beginning_found = False
        self._found_title = False
        
        self._found_h3_tag = False
        
        self._parse_URLs()
    
    def __unicode__(self):
        return u"Soundcloud"
    
    def _download_page(self):
        response = urllib2.urlopen(path.join(self._url, "tracks")).read()
        return unicode(response, "utf-8")
    
    def handle_starttag(self, tag, attrs):
        self._convert_attrs_list_to_dict(attrs)
        
        if tag == "h3":
            self._found_h3_tag = True
        
        # extract link and description in meta-tags
        # see next comment to see what happens, if they dont exist
        if tag == "meta" and self._attrs_dict.has_key("itemprop"):
            if self._attrs_dict["itemprop"] == "url":
                self._act_info["link"] = self._attrs_dict["content"]
                
            if self._attrs_dict["itemprop"] == "description":
                self._act_info["description"] = self._attrs_dict["content"]
        
        # search for beginning of title
        #
        # additional Fallback for link. if no meta-tags exist
        # (description cant be parsed otherwise than by meta-tags
        #  → wont exist if no meta tags are found)
        if (tag == "a" and self._attrs_dict.has_key("href")
            and self._found_h3_tag):
            self._found_title = True
            
            #if self._act_info["link"] == None:
            self._act_info["link"] = "https://soundcloud.com" +\
                                         self._attrs_dict["href"] 
        
        # search pubDate
        if (tag == "abbr" and self._attrs_dict.has_key("class") and
            self._attrs_dict.has_key("title")):
            if self._attrs_dict["class"] == "pretty-date":
                locale.setlocale(locale.LC_TIME, "C")
                # datetime.strptime doesnt support %z in python 2.x
                # see http://bugs.python.org/issue6641
                pubDate = datetime.strptime(self._attrs_dict["title"][:-6],
                            "%B, %d %Y %H:%M:%S")#.replace(tzinfo=None)
                self._act_info["pubDate"] = pubDate
        
        if (self._act_info["title"] != "" and
                self._act_info["link"] != None and
                self._act_info["pubDate"] != None):
            self._next_url_info()
        
    def handle_data(self, data):
        if self._found_title:
            self._act_info["title"] += data
        
    def handle_endtag(self, tag):
        if tag == "a" and self._found_title:
            self._found_title = False
            
        if tag == "h3" and self._found_h3_tag:
            self._found_h3_tag = False
    
    
class TwitterParser(GenericParser):
    def __init__(self, url):
        GenericParser.__init__(self, url)
        
        self.__found_description = False
        
        self.__found_twitter_username = False
        self.__twitter_username = u""
        
        self._parse_URLs()
    
    def __unicode__(self):
        return u"Twitter"
    
    def handle_starttag(self, tag, attrs):
        self._convert_attrs_list_to_dict(attrs)
        
        # search username
        if tag == "a" and self._attrs_dict.has_key("class"):
            if "ProfileHeaderCard-nameLink" in self._attrs_dict["class"]:
                self.__found_twitter_username = True
        
        # search link and pubDate
        if (tag == "a" and self._attrs_dict.has_key("title") and
             self._attrs_dict.has_key("href") and
             self._attrs_dict.has_key("class")):
            if "ProfileTweet-timestamp" in self._attrs_dict["class"]:
                self._act_info["link"] = "https://twitter.com" +\
                                         self._attrs_dict["href"]
                
                # locale needed for correct date parsing (→ month name)
                locale.setlocale(locale.LC_TIME, "")
                try:
                    self._act_info["pubDate"] = datetime.strptime(
                                            self._attrs_dict["title"],
                                            "%H:%M - %d. %b. %Y")
                except ValueError:
                    try:
                        self._act_info["pubDate"] = datetime.strptime(
                                            self._attrs_dict["title"],
                                            "%H:%M - %d. %B %Y")
                    except ValueError:
                        raise
                
                # create title after required data (username and pubDate)
                # are collected
                self._act_info["title"] = u"[" + self.__twitter_username +\
                                "] Tweet " +\
                                self._act_info["pubDate"].isoformat(" ")
        
        # search beginning of description
        if tag == "p" and self._attrs_dict.has_key("class"):
            if "ProfileTweet-text" in self._attrs_dict["class"]:
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
    soundcloud = SoundcloudParser(u"https://soundcloud.com/calvinharris")
    soundcloud_test = soundcloud.getData()
    print soundcloud_test
    
    twitter_test = TwitterParser(u"https://twitter.com/ubernauten").getData()
    
    #for t in soundcloud_test, twitter_test:
    #    print "###########################################################"
    #    for i in t:
    #        print i["title"]
    #        print i["link"]
    #        print i["pubDate"]
    #        print i["description"]
    #        print "--------------------------------------------------------"
