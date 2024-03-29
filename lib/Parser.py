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
        try:
            response = urllib.request.urlopen(request).read()
        except (urllib.error.HTTPError, urllib.error.URLError) as error:
            print(error, "on", self._url)
            return ""
        else:
            return str(response, "utf-8")

    def _parse_URLs(self):
        content = self._download_page()
        if not content:
            return
        self.feed(content)

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
        self.__inside_style = False
        self.__inside_heading = False

        self._parse_URLs()

        for elem in self._list_url_info:
            parser = DescriptionParser(elem["link"])
            elem["description"] = parser.getData()

    def __str__(self):
        return "SZ"

    def handle_starttag(self, tag, attrs):
        if tag == "article":
            self.__found_entry = True
 
        if self.__found_entry and tag == "a":
            attrs = self._attrs_to_dict(attrs)
            self._act_info["link"] = attrs["href"]

        if self.__found_entry and tag == "time":
            attrs = self._attrs_to_dict(attrs)
            self._act_info["pubDate"] = datetime.fromisoformat(attrs.get("datetime"))

        if tag == "style":
            self.__inside_style = True

        if tag == "h3":
            self.__inside_heading = True

    def handle_data(self, data):
        if self.__found_entry and self.__inside_heading and not self.__inside_style:
            self._act_info["title"] += data

    def handle_endtag(self, tag):
        if tag == "article" and self.__found_entry:
            self.__found_entry = False

            self._act_info["title"] = self.rm_whitespace(self._act_info["title"])

            self._next_url_info()

        if tag == "style":
            self.__inside_style = False

        if tag == "h3" and self.__inside_heading:
            self.__inside_heading = False

class FunkParser(GenericParser):
    def __init__(self, channel_id):
        self.channel_id = channel_id
        url = f"https://www.funk.net/api/frontend/webapp/video-channels/{channel_id}/videos?page=0&size=10"
        super().__init__(url)

        self.json_response = self._download_page()
        self.handle_json()

    def __str__(self):
        return "Funk"

    def handle_json(self):
        try:
            python_struct = json.loads(self.json_response)
        except json.decoder.JSONDecodeError as error:
            print(error, "on", self._url)
            return

        for element in python_struct["list"]:
            self._act_info["title"] = element["title"]
            self._act_info["description"] = element["shortDescription"]

            video_alias = element["alias"]
            channel_alias = element["channelAlias"]
            link = f"https://www.funk.net/channel/{channel_alias}/{video_alias}"
            self._act_info["link"] = link

            # f.e. '2022-10-20T18:00:00Z'
            pubdate = datetime.strptime(
                element["publicationDate"], "%Y-%m-%dT%H:%M:%S%z"
            )
            self._act_info["pubDate"] = pubdate

            self._next_url_info()
