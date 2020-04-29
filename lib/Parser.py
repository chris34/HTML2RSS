#!/usr/bin/env python3

from copy import deepcopy
from datetime import datetime
import urllib.request
import urllib.error
import urllib.parse
from urllib.parse import urljoin
import json
import re


from html.parser import HTMLParser


class GenericParser(HTMLParser):
    """Basic tools to collect information from a single webpage (→ self._url)"""

    def __init__(self, url):
        super().__init__()
        self._url = url

        self.__template_item_info = {
            "title": "",
            "link": None,
            "description": "",
            "source": self._url,
            "pubDate": None,
        }
        self._list_url_info = []

        self._act_info = deepcopy(self.__template_item_info)

    def _attrs_to_dict(self, attrs_list):
        """Converts HTMLParser's attrs list to an dict. Thus, a check,
        whether a attribute exists, is simplified via has_key()"""
        attrs_dict = {}

        for key, value in attrs_list:
            attrs_dict[key] = value

        return attrs_dict

    def _download_page(self):
        request = urllib.request.Request(
            self._url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en"}
        )
        response = urllib.request.urlopen(request).read()
        return str(response, "utf-8")

    def _parse_URLs(self):
        try:
            self.feed(self._download_page())
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            print(error, "on", self._url)

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


class DescriptionParser:
    """
    Downloads url, all content of <main> can be retrieved with `getData`.
    Helps to get a description of an feed entry.
    """

    def __init__(self, url):
        self.page = GenericParser(url)._download_page()

        re_flags = re.DOTALL | re.IGNORECASE

        matches = re.search(r"<main>.+</main>", self.page, re_flags)
        self.page = matches.group(0)

        # Try to remove some scripts. Not secure at all.
        self.page = re.sub(r"<script.*?</script>", "", self.page, flags=re_flags)

    def getData(self):
        return self.page


class SoundcloudDescriptionParser(GenericParser):
    def __init__(self, url):
        super().__init__(url)

        self._inside_article = False
        self._description_text = ""

        self._parse_URLs()

    def getData(self):
        return self._description_text

    def handle_starttag(self, tag, attrs):
        if tag == "article":
            self._inside_article = True
            return

        if tag == "meta" and self._inside_article:
            attrs = self._attrs_to_dict(attrs)
            if (
                "itemprop" in attrs
                and attrs["itemprop"] == "description"
                and "content" in attrs
            ):
                self._description_text = attrs["content"]

    def handle_endtag(self, tag):
        if tag == "article" and self._inside_article:
            self._inside_article = False


class SoundcloudParser(GenericParser):
    def __init__(self, url):
        super().__init__(url)

        self._found_track = False

        self._collect_pubdate = False
        self._pubdate_string = ""

        self._collect_title = False
        self._title_string = ""

        self._parse_URLs()

        for elem in self._list_url_info:
            parser = SoundcloudDescriptionParser(elem["link"])
            elem["description"] = parser.getData()

    def __str__(self):
        return "Soundcloud"

    def _next_url_info(self):
        GenericParser._next_url_info(self)

        self._pubdate_string = ""
        self._title_string = ""

    def handle_starttag(self, tag, attrs):
        attrs = self._attrs_to_dict(attrs)

        if tag == "article" and "class" in attrs and attrs["class"] == "audible":
            self._found_track = True

        if self._found_track:
            if tag == "a" and "itemprop" in attrs and attrs["itemprop"] == "url":
                self._act_info["link"] = urljoin(self._url, attrs["href"])
                self._collect_title = True

            if tag == "time" and "pubdate" in attrs:
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

            try:
                self._act_info["pubDate"] = datetime.fromisoformat(
                    # strip last Z
                    self._pubdate_string[:-1]
                )
            except ValueError as e:
                self._act_info["pubDate"] = datetime.strptime(
                    self._pubdate_string, "%Y/%m/%d  %H:%M:%S%z"
                )


class TwitterParser(GenericParser):
    def __init__(self, url):
        super().__init__(url)

        self.__found_description = False

        self.__found_twitter_username = False
        self.__twitter_username = ""

        self._parse_URLs()

    def __str__(self):
        return "Twitter"

    def handle_starttag(self, tag, attrs):
        attrs = self._attrs_to_dict(attrs)

        # search username
        if tag == "a" and "class" in attrs:
            if "ProfileHeaderCard-nameLink" in attrs["class"]:
                self.__found_twitter_username = True

        # search link and pubDate
        if tag == "a" and "title" in attrs and "href" in attrs and "class" in attrs:
            if "tweet-timestamp" in attrs["class"]:
                self._act_info["link"] = "https://twitter.com" + attrs["href"]

                date_string = attrs["title"]

                # example format: '2:07 PM - 3 Oct 2014'
                self._act_info["pubDate"] = datetime.strptime(
                    date_string, "%I:%M %p - %d %b %Y"
                )

                # create title after required data (username and pubDate)
                # are collected
                self._act_info["title"] = (
                    "["
                    + self.__twitter_username
                    + "] Tweet "
                    + self._act_info["pubDate"].isoformat(" ")
                )

        # search beginning of description
        if tag == "p" and "class" in attrs:
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


class IdParser(GenericParser):
    def __init__(self, url):
        super().__init__(url)

        self._id_found = False

        self._tag = "a"
        self._id = "link_archive"

        self._parse_URLs()

    def __str__(self):
        return "ID"

    def handle_starttag(self, tag, attrs):
        if tag == self._tag:
            attrs = self._attrs_to_dict(attrs)
            if attrs.get("id") == self._id:
                self._id_found = True

                link = urljoin(self._url, attrs["href"])
                self._act_info["link"] = link
                self._act_info["pubDate"] = datetime.now()
        elif tag == "img" and self._id_found:
            attrs = self._attrs_to_dict(attrs)
            src = urljoin(self._url, attrs["src"])
            self._act_info["description"] = f'<img src="{ src }" />'

    def handle_endtag(self, tag):
        if tag == self._tag and self._id_found:
            self._id_found = False
            self._next_url_info()


class SzParser(GenericParser):
    def __init__(self, url):
        super().__init__(url)

        self.__found_entry = False

        self._parse_URLs()

        for elem in self._list_url_info:
            parser = DescriptionParser(elem["link"])
            elem["description"] = parser.getData()

    def __str__(self):
        return "SZ"

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs = self._attrs_to_dict(attrs)
            if attrs.get("class") == "sz-teaser":
                self.__found_entry = True
                self._act_info["link"] = attrs["href"]
                self._act_info["pubDate"] = datetime.now()

    def handle_data(self, data):
        if self.__found_entry:
            self._act_info["title"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.__found_entry:
            self.__found_entry = False
            self._act_info["title"] = self.rm_whitespace(self._act_info["title"])
            self._next_url_info()


class FunkParser(GenericParser):
    def __init__(self, channel_id):
        self.channel_id = channel_id
        url = f"https://www.funk.net/data/videos/byChannelAlias/{channel_id}?page=0&size=10"
        super().__init__(url)

        self.json_response = self._download_page()
        self.handle_json()

    def __str__(self):
        return "Funk"

    def handle_json(self):
        python_struct = json.loads(self.json_response)

        for element in python_struct["list"]:
            self._act_info["title"] = element["title"]
            self._act_info["description"] = element["shortDescription"]

            video_alias = element["alias"]
            link = f"https://www.funk.net/channel/{self.channel_id}/{video_alias}"
            self._act_info["link"] = link

            # f.e. 2020-01-13T19:09:30.000+0000
            pubdate = datetime.strptime(
                element["publicationDate"], "%Y-%m-%dT%H:%M:%S.000%z"
            )
            self._act_info["pubDate"] = pubdate

            self._next_url_info()


if __name__ == "__main__":
    print("Small manual test")

    soundcloud = SoundcloudParser("https://soundcloud.com/soundcloud")
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
    twitter = TwitterParser("https://twitter.com/twitter")
    twitter_test = twitter.getData()

    for t in soundcloud_test, twitter_test:
        print("###########################################################")
        for i in t:
            print(i["title"])
            print(i["link"])
            print(i["pubDate"])
            print(i["description"])
            print("--------------------------------------------------------")
