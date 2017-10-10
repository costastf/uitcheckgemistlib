#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: uitcheckgemistlib.py
#
# Copyright 2017 Costas Tyfoxylos
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
#

"""
Main code for uitcheckgemistlib

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""

import logging
from requests import Session
from bs4 import BeautifulSoup as bfs
from dateutil.parser import parse
from collections import namedtuple

__author__ = '''Costas Tyfoxylos <costas.tyf@gmail.com>'''
__docformat__ = '''google'''
__date__ = '''2017-10-08'''
__copyright__ = '''Copyright 2017, Costas Tyfoxylos'''
__credits__ = ["Costas Tyfoxylos"]
__license__ = '''MIT'''
__maintainer__ = '''Costas Tyfoxylos'''
__email__ = '''<costas.tyf@gmail.com>'''
__status__ = '''Development'''  # "Prototype", "Development", "Production".


# This is the main prefix used for logging
LOGGER_BASENAME = '''uitcheckgemistlib'''
LOGGER = logging.getLogger(LOGGER_BASENAME)
LOGGER.addHandler(logging.NullHandler())


Quadrants = namedtuple('Quadrants', ['first', 'second', 'third', 'forth'])


class Server(object):

    def __init__(self, card_number, valid_until, birth_date):
        self._base_url = 'https://www.uitcheckgemist.nl/'
        self._data_url = None
        self._card = OvChipCard(card_number, valid_until)
        self._birth_date = birth_date
        self._missed_checks = None
        self._headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        self._session = Session()
        self._authenticate()

    def _authenticate(self):
        response = self._submit_card_details()
        response = self._submit_personal_information(response)
        self._missed_checks = self._parse_missed_checks(response)

    def _submit_card_details(self):
        response = self._session.get(self._base_url)
        token = self._get_token(response, 'tls_card_information[_token]')
        data = {'tls_card_information[_token]': token,
                'tls_card_information[engravedId][0]':
                    self._card.quadrants.first,
                'tls_card_information[engravedId][1]':
                    self._card.quadrants.second,
                'tls_card_information[engravedId][2]':
                    self._card.quadrants.third,
                'tls_card_information[engravedId][3]':
                    self._card.quadrants.forth,
                'tls_card_information[expirationDate]': self._card.valid_until,
                'tls_card_information[optIn]': 1}
        response = self._session.post(self._base_url,
                                      data=data,
                                      headers=self._headers)
        return response

    def _submit_personal_information(self, response):
        token = self._get_token(response, 'tls_person_information[_token]')
        data = {'tls_person_information[_token]': token,
                'tls_person_information[holderBirthDate]': self._birth_date}
        response = self._session.post(response.url,
                                      data=data,
                                      headers=self._headers)
        redirect = response.history[0].headers.get('Location')
        self._data_url = self._trim_slash(self._base_url) + redirect
        return response

    @staticmethod
    def _trim_slash(data):
        data = data[:-1] if data.endswith('/') else data
        return data

    @staticmethod
    def _get_token(response, name):
        soup = bfs(response.text, 'html.parser')
        token = soup.find('input', {'name': name}).attrs.get('value')
        return token

    @property
    def missed_checks(self):
        return self._missed_checks

    def _parse_missed_checks(self, response):
        self._response = response
        transactions = []
        return transactions

    def get_latest_missed_checks(self):
        _ = self.missed_checks  # noqa
        missed_checks = self._missed_checks[:]
        self._missed_checks = []
        return missed_checks


class OvChipCard(object):

    def __init__(self, card_number, valid_until):
        self.number = self._validate_number(card_number)
        self.valid_until = self._validate_date(valid_until)
        self.quadrants = Quadrants(*self.number.split('-'))

    @staticmethod
    def _validate_number(card_number):
        card_number = ''.join([character for character in card_number
                               if character.isdigit()])
        if not len(card_number) == 16 or not card_number[:4] == '3528':
            raise ValueError('Invalid card number :{}'.format(card_number))
        number = '-'.join(map(''.join, zip(*[iter(card_number)] * 4)))
        return number

    def __str__(self):
        text = ('Number      :{}'.format(self.number),
                'Valid Until :{}'.format(self.valid_until))
        return '\n'.join(text)

    @staticmethod
    def _validate_date(valid_until):
        try:
            date_ = parse(valid_until)
        except ValueError:
            raise ValueError('Invalid "valid until" date provided')
        return date_.strftime('%d-%m-%Y')

