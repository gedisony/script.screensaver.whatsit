# coding: utf8
"""
:mod:`boardgamegeek.search` - Search results
============================================

.. module:: boardgamegeek.search
   :platform: Unix, Windows
   :synopsis: classes for handling search results

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>

"""
from __future__ import unicode_literals

from .exceptions import BoardGameGeekError
from .things import Thing


class SearchResult(Thing):
    """
    Result of a search
    """

    def __init__(self, data):
        if "yearpublished" in data:
            if type(data["yearpublished"]) not in [int, type(None)]:
                raise BoardGameGeekError("yearpublished is not valid")
        super(SearchResult, self).__init__(data)

    def _format(self, log):
        log.info("searched item id   : {}".format(self.id))
        log.info("searched item name : {}".format(self.name))
        log.info("searched item type : {}".format(self.type))
        log.info("searched item year : {}".format(self.year))

    @property
    def type(self):
        return self._data["type"]

    @property
    def year(self):
        return self._data.get("yearpublished")
