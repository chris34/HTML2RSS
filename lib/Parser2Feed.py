#!/usr/bin/env python3

from os import path, mkdir

from .atom_generator import AtomFeed
from .Parser import IdParser, SoundcloudParser, SzParser, TwitterParser


class GenericParser2FeedHandler:
    def __init__(self, config):
        self._config = config

        self._feed_dict = {} # template: {'Filename': AtomFeed-object}

        self._create_feed()
        self.__write_feed_2_file()

    def __write_feed_2_file(self):
        for feed_path, feed_object in list(self._feed_dict.items()):
            feed_object.sort_items_after_date()

            # check directory
            feed_path = path.expanduser(feed_path)
            dir_path = path.dirname(feed_path)
            if not path.exists(dir_path):
                mkdir(dir_path)

            with open(feed_path, "w") as f:
                f.write(feed_object.getFeed())

    def _create_feed(self):
        pass

    def _choose_parser(self, config_section):
        config_parser = self._config[config_section]["parser"]

        if config_parser == "idparser":
            return IdParser(self._config[config_section]["source-url"])
        elif config_parser == "soundcloud":
            return SoundcloudParser(
                            self._config[config_section]["source-url"])
        elif config_parser == "szparser":
            return SzParser(self._config[config_section]["source-url"])
        elif config_parser == "twitter":
            return TwitterParser(
                            self._config[config_section]["source-url"])
        else:
            raise NoParserError(config_parser, config_section)


class OneRSSFile(GenericParser2FeedHandler):
    def _create_feed(self):
        feed = AtomFeed(self._config["GENERAL"]["feed-title"],
                      self._config["GENERAL"]["feed-url"],
                      self._config["GENERAL"]["feed-description"])

        for i in self._config:
            if i != "GENERAL":
                parser = self._choose_parser(i)

                for d in parser.getData():
                    feed.addItem(d["title"], d["link"], d["description"],
                                 d["pubDate"], d["source"])

                feed_location = self._config["GENERAL"]["feed-location"]
                self._feed_dict[path.join(feed_location, 'feed.xml')] = feed


class RSSFilePerParser(GenericParser2FeedHandler):
    def _create_feed(self):
        parser_dict = {}

        for i in self._config:
            if i != "GENERAL":
                parser = self._choose_parser(i)
                parser_name = str(parser)

                if parser_name in list(parser_dict.keys()):
                    parser_dict[parser_name].append(parser)
                else:
                    parser_dict[parser_name] = [parser]

        for i in parser_dict:
            feed = AtomFeed(self._config["GENERAL"]["feed-title"],
                    self._config["GENERAL"]["feed-url"],
                    self._config["GENERAL"]["feed-description"])

            for p in parser_dict[i]:
                for d in p.getData():
                    feed.addItem(d["title"], d["link"], d["description"],
                                 d["pubDate"], d["source"])

            feed_location = self._config["GENERAL"]["feed-location"]
            full_path = path.join(feed_location,
                                           'feed-%s.xml' %i)
            self._feed_dict[full_path] = feed


class RSSFilePerURL(GenericParser2FeedHandler):
    def _create_feed(self):
        for i in self._config:
            if i != "GENERAL":
                feed = AtomFeed(self._config["GENERAL"]["feed-title"],
                      self._config["GENERAL"]["feed-url"],
                      self._config["GENERAL"]["feed-description"])

                parser = self._choose_parser(i)

                for d in parser.getData():
                    feed.addItem(d["title"], d["link"], d["description"],
                                 d["pubDate"], d["source"])

                feed_location = self._config["GENERAL"]["feed-location"]
                full_path = path.join(feed_location,
                                           'feed-%s.xml' %i)
                self._feed_dict[full_path] = feed


class NoParserError(Exception):
    def __init__(self, parsername, config_section):
        self.parsername = parsername
        self.config_section = config_section

    def __str__(self):
        return repr('You wanted to use a parser named "%s" in the\
configsection "%s". However, this parser does not exists (yet).' %(
                                self.parsername, self.config_section))
