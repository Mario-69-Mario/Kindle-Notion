#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Creates Evernote notes for all of your Kindle highlights.

Requires an Evernote developer account (see readme) and a corresponding
authorization token, and an HTML file of all your Kindle highlights from
kindle.amazon.com.

Example usage:

python whispernote.py auth_token.txt myhighlights.html

# no libraries: hashlib, binascii
"""

import argparse
from bs4 import BeautifulSoup
import datetime
import logging
from logging.config import dictConfig
from pyfiglet import Figlet
import re
from time import sleep
#import urlparse
import urllib.parse


class KindleHighlights(object):
    """ Object input is a kindle.amazon.com highlights HTML file.

    The highlights attribute is a list of dicts, where each dict is a highlight,
    including book_author, text, book_title, link, and ID.

    The parsed attribute is the highlights HTML file with hierarchy.
    """

    def __init__(self, html_file):
        self._highlights = self._get_all_highlights(html_file)

        self.logger = logging.getLogger('whispernote')
        self.logger.info('Initializing Kindle Highlights')


    def __repr__(self):
        return self._highlights


    def __iter__(self):
        for hl in self._highlights:
            yield hl


    def __getitem__(self, i):
        return self._highlights[i]


    def _create_enid(self, huri): 
        """
        Creates an Evernote unique ID based on the highlight's URI. 
        A Kindle highlight is composed of a 'asin', or ISBN of the book, 
        and a location. 

        huri - highlight URI

        kindle://book?action=open&asin=B004TP29C4&location=4063

        will return...

        B004TP29C44063
        """

        asin = urllib.parse(huri).query.split('&')[1].split('=')[1]
        loc = urllib.parse(huri).query.split('&')[2].split('=')[1]

        return asin + loc


    def _get_all_highlights(self, html_file):
        html_doc = open(html_file, 'r').read()
        parsed = self._parse_books(html_doc)
        return self._extract_highlights(parsed)


    def _parse_books(self, html):
       """ Pass in the HTML from the myhighlights.html page, and function adds 
       hierarchy to page. All of a book's highlights divs are subsumed beneath
       the book itself. This allows the highlights to include general book 
       information (title and author). Outputs an html string.
       """
       markup = list(html.split('\n'))

       # Add highlightColumn hierarchy
       for i, line in enumerate(markup):
           if 'class="bookMain yourHighlightsHeader"' in line:
               markup[i] = '</div>' + line + '<div class="highlightColumn">'
       # Remove the very first </div>
       try:
           all_hl_div = (i for i, line in enumerate(markup) 
                         if re.search('.*<div id="allHighlightedBooks">.*', line)
                        ).next()
       except StopIteration:
           print('Did not find DIV id="allHighlightedBooks"')
           raise
       markup[all_hl_div] = markup[all_hl_div].replace('</div>', '')

       new_markup = ''.join(markup)

       return new_markup


    def _extract_highlights(self, html):
        """
        Returns an array of highlight dictionaries - content, link,
        and generated IDs - for all books.
        """

        # Initialize container
        hdicts = []

        # Find all book info divs
        soup = BeautifulSoup(html, 'html.parser')
        books = soup.find_all('div', 'bookMain')

        # Gather book information and highlights
        for book in books:
            book_title = book.find('span', 'title').string.strip()
            book_author = (book.find('span', 'author').string
                           .replace('by', '').strip())
            book_highlights = book.find_all('span', 'highlight')

            # Gather highlights from a specific book
            for highlight in book_highlights:
                hdicts.append(
                    dict(
                        book_title=book_title,
                        book_author=book_author,
                        text=highlight.string,
                        link=highlight.nextSibling.attrs['href'],
                        id=self._create_enid(highlight
                                              .nextSibling.attrs['href'])
                    )
                )

        return hdicts


def now_plus_seconds(seconds):
    """ Gets current time and adds x seconds
    """
    now = datetime.datetime.now()
    future = now + datetime.timedelta(seconds=seconds)
    future_time = future.time()
    return future_time.strftime('%H:%M:%S')


def ascii_art(text, font='standard'):
    """ Prints important messages in  large ASCII font.
    """
    f = Figlet(font=font)
    print('\n')
    print(f.renderText(text))


def limit_exceeded():
    ascii_art('API   Limit\nExceeded')


def validate_html(html):
    """ Convert offensive characters to HTML entities, e.g., '&' to '&amp;'
    """
    bs = BeautifulSoup(html, 'html.parser')
    return bs.prettify(formatter='html')


def generate_logger(debug=False):

    if debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.WARN

    logging_config = dict(
        version=1,
        formatters={
            'f': {'format':
                  '%(asctime)s - %(levelname)s - %(message)s'}
        },
        handlers={
            'h': {'class': 'logging.StreamHandler',
                  'formatter': 'f',
                  'level': log_level}
        },
        root={
            'handlers': ['h'],
            'level': log_level,
         },
    )

    dictConfig(logging_config)
    logger = logging.getLogger()

    return logger


def retrieve_arguments():

    app_description = 'Add Kindle Highlights to your Evernote account'
    parser = argparse.ArgumentParser(description=app_description)
    parser.add_argument('highlights', type=str,
                        help='Kindle highlights HTML document')
    parser.add_argument('api_key_file', type=str,
                        help='Text file containing Evernote dev key')
    parser.add_argument('-n', '--notebook', type=str,
                        help='EverNote notebook to add Kindle highlights')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print verbose output')
    return parser.parse_args()

def main():

    auth_token = open('en_auth.txt', 'r').read()
    #evernote = EvernoteAPI(auth_token, args.notebook)
    highlights = KindleHighlights('https://read.amazon.com/notebook')
    #evernote.add_notes(highlights)


if __name__ == '__main__':
    #args = retrieve_arguments()
    #'myhighlights.html en_auth.txt'
    #logger = generate_logger(args.verbose)
    main()
