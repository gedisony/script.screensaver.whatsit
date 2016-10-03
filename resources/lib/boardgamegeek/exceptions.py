# coding: utf-8
"""
:mod:`boardgamegeek.exceptions` - Exceptions
============================================

.. module:: boardgamegeek.exceptions
   :platform: Unix, Windows
   :synopsis: exceptions used in the package

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>
"""

# boardgamegeek library base exception
class BoardGameGeekError(Exception):
    pass


class BoardGameGeekTimeoutError(BoardGameGeekError):
    pass


class BoardGameGeekAPIError(BoardGameGeekError):
    pass


class BoardGameGeekAPIRetryError(BoardGameGeekAPIError):
    pass


class BoardGameGeekAPINonXMLError(BoardGameGeekAPIError):
    pass
