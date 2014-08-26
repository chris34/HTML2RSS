# What this program does and why
As already written in the description, this program downloads specified URLs, parses HTML and writes the parsed information to an atom-feed. At the moment it supports soundcloud-track-streams and twitter-user-streams.

Thus, you do not need any account or login to be up to date what is happening on these sites. You just need a RSS-reader and an Internet-connection.

# Dependencies
The only dependency you need to run this script is Python 2.x. If you have not installed it already, you can simply do this under an Debian-like OS by running

    sudo apt-get install python

# Installation
Simply download (or clone) this repository. You're done!

# Usage
To run the program once, you can simply run

    python Main.py

in an terminal. 

For periodically usage – imho the main task – you can run it with the help of cron, runwhen or equivalent software. See their documentation on how to use it, please. ;)

For further configuration – f.e. which sites should be parsed – see config/html2rss.cfg.default. This file should be good documented itself.

# HTTP-Error-Handling
If the download of a page fails with f.e. a 503 “Service Unavailable”, a error message with the pageurl and statuscode will be directly printed to stdout. Additionally, the page will be skipped in this run.
