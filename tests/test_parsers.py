import unittest

from datetime import datetime
from lib.Parser import *


class TestParser(unittest.TestCase):
    def test_funk(self):
        elements = FunkParser("12068").getData()

        self.assertGreater(len(elements), 0)
        for e in elements:
            with self.subTest(element=e):
                self.assertNotEqual(e["title"], "")
                self.assertIsNotNone(e["link"])
                self.assertIsInstance(e["pubDate"], datetime)
                self.assertNotEqual(e["description"], "")

    def test_sz(self):
        elements = SzParser("https://www.sueddeutsche.de/thema/SZ_Espresso").getData()

        self.assertGreater(len(elements), 0)
        for e in elements:
            #print(e["title"], e["pubDate"], "\n")
            with self.subTest(element=e):
                self.assertNotEqual(e["title"], "")
                self.assertIsNotNone(e["link"])
                self.assertIsInstance(e["pubDate"], datetime)
                self.assertNotEqual(e["description"], "")

    def test_id(self):
        elements = IdParser("https://ruthe.de/").getData()

        self.assertGreater(len(elements), 0)
        for e in elements:
            with self.subTest(element=e):
                self.assertEqual(e["title"], "")
                self.assertIsNotNone(e["link"])
                self.assertIsInstance(e["pubDate"], datetime)
                self.assertNotEqual(e["description"], "")

    def test_soundcloud(self):
        elements = SoundcloudParser("https://soundcloud.com/anjunadeep").getData()

        self.assertGreater(len(elements), 0)
        for e in elements:
            with self.subTest(element=e):
                self.assertNotEqual(e["title"], "")
                self.assertIsNotNone(e["link"])
                self.assertIsInstance(e["pubDate"], datetime)
                self.assertNotEqual(e["description"], "")
