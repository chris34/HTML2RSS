import unittest
from unittest.mock import patch
from datetime import datetime

from lib.atom_generator import AtomFeed


class TestGenerators(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()

        patcher = patch(
            "lib.atom_generator.formatdate",
            return_value="Fri, 09 Nov 2001 01:08:47 -0000",
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.feed = AtomFeed("Test", "http://example.org", "Just for test purposes")

    def test_feed_generation__one_item(self):
        self.feed.addItem(
            "Testarticle",
            "http://example.org/article",
            "Article description should normally be here!",
        )

        self.assertEqual(
            self.feed.getFeed(),
            """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">

<channel>
        <title>Test</title>
        <link>http://example.org</link>
        <description>Just for test purposes</description>
        <pubDate>Fri, 09 Nov 2001 01:08:47 -0000</pubDate>

        <atom:link href="http://example.org" rel="self" type="application/rss+xml"/> 

    <item>
        <title>Testarticle</title>
        <link>http://example.org/article</link>
        <description>Article description should normally be here!</description>
    </item>
</channel>

</rss>""",
        )

    def test_feed_generation__two_items(self):
        for i in range(0, 2):
            title = "Testarticle %s" % i
            self.feed.addItem(
                title,
                "http://example.org/article",
                "Article description should normally be here!",
            )

        self.assertEqual(
            self.feed.getFeed(),
            """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">

<channel>
        <title>Test</title>
        <link>http://example.org</link>
        <description>Just for test purposes</description>
        <pubDate>Fri, 09 Nov 2001 01:08:47 -0000</pubDate>

        <atom:link href="http://example.org" rel="self" type="application/rss+xml"/> 

    <item>
        <title>Testarticle 0</title>
        <link>http://example.org/article</link>
        <description>Article description should normally be here!</description>
    </item>
    <item>
        <title>Testarticle 1</title>
        <link>http://example.org/article</link>
        <description>Article description should normally be here!</description>
    </item>
</channel>

</rss>""",
        )

    def test_feed_generation__publication_date(self):
        for i in range(0, 2):
            title = "Testarticle with source and pubDate %s" % i
            self.feed.addItem(
                title,
                "http://example.org/article",
                "Article description should normally be here!",
                datetime.now(),
                "http://example.org/list-articles",
            )

        self.assertEqual(
            self.feed.getFeed(),
            """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">

<channel>
        <title>Test</title>
        <link>http://example.org</link>
        <description>Just for test purposes</description>
        <pubDate>Fri, 09 Nov 2001 01:08:47 -0000</pubDate>

        <atom:link href="http://example.org" rel="self" type="application/rss+xml"/> 

    <item>
        <title>Testarticle with source and pubDate 0</title>
        <link>http://example.org/article</link>
        <description>Article description should normally be here!</description>
        <pubDate>Fri, 09 Nov 2001 01:08:47 -0000</pubDate>
    </item>
    <item>
        <title>Testarticle with source and pubDate 1</title>
        <link>http://example.org/article</link>
        <description>Article description should normally be here!</description>
        <pubDate>Fri, 09 Nov 2001 01:08:47 -0000</pubDate>
    </item>
</channel>

</rss>""",
        )
