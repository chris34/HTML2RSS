#!/usr/bin/env python
# -*- coding: utf-8 -*-


from codecs import open
import ConfigParser
from os import path
from sys import argv

from lib.Parser2Feed import OneRSSFile, RSSFilePerParser, RSSFilePerURL

class Main(object):
    def __init__(self):
        self.__config = ConfigParser.SafeConfigParser()

        working_path = path.dirname(argv[0])
        default_config = path.join(working_path,
                                   "config/html2rss.cfg.default")

        self.__config.readfp(open(default_config, "r", encoding="utf8"))
        self.__config.read(path.join(working_path,"config/html2rss.cfg"))
        self.__config_dict = self.__convert_config_to_dict()

        self.__choose_handler()

    def __convert_config_to_dict(self):
        config_dict = {}

        for sec in self.__config.sections():
            sec_dict = {}

            for key, value in self.__config.items(sec):
                key = to_unicode_or_burst(key)
                value = to_unicode_or_burst(value)

                sec_dict[key] = value

            config_dict[to_unicode_or_burst(sec)] = sec_dict

        return config_dict

    def __choose_handler(self):
        mode =  self.__config_dict["GENERAL"]["feed-mode"]

        if mode == "one-feed-for-all":
            OneRSSFile(self.__config_dict)
        elif mode == "one-feed-per-parser":
            RSSFilePerParser(self.__config_dict)
        elif mode == "one-feed-per-url":
            RSSFilePerURL(self.__config_dict)
        else:
            raise NoModeError(mode, "GENERAL")


class NoModeError(Exception):
    def __init__(self, mode, config_section):
        self.mode = mode
        self.config_section = config_section

    def __str__(self):
        return repr('You wanted to use a mode named "%s" in the configsection "%s". However, this mode does not exists (yet).' %(self.mode, self.config_section))


def to_unicode_or_burst(obj, encoding="utf-8"):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj


if __name__ == "__main__":
    Main()
