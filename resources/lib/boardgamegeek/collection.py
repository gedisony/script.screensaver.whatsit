# coding: utf-8
"""
:mod:`boardgamegeek.collection` - Collection information
========================================================

.. module:: boardgamegeek.collection
   :platform: Unix, Windows
   :synopsis: classes for storing collection information

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>

"""
from __future__ import unicode_literals
from copy import copy

from .exceptions import BoardGameGeekError
from .games import CollectionBoardGame
from .utils import DictObject


class Collection(DictObject):
    """
    A dictionary-like object represeting a ``Collection``

    :param dict data: a dictionary containing the collection data
    :raises: :py:class:`boardgamegeek.exceptions.BoardGameGeekError` in case of invalid data
    """
    def __init__(self, data):
        kw = copy(data)

        if "items" not in kw:
            kw["items"] = []

        self._items = []
        self.__game_ids = set()

        for i in kw["items"]:
            try:
                if i["id"] not in self.__game_ids:
                    self.__game_ids.add(i["id"])
                    self._items.append(CollectionBoardGame(i))
            except KeyError:
                raise BoardGameGeekError("invalid game data")

        super(Collection, self).__init__(kw)

    def _format(self, log):
        log.info("owner    : {}".format(self.owner))
        log.info("size     : {} items".format(len(self)))

        log.info("items")

        for i in self:
            i._format(log)
            log.info("")

    def add_game(self, game):
        """
        Add a game to the ``Collection``

        :param dict game: game data
        :raises: :py:class:`boardgamegeek.exceptions.BoardGameGeekError` in case of invalid data
        """
        try:
            # Collections can have duplicate elements (different collection ids), so don't add the same thing multiple times
            if game["id"] not in self.__game_ids:
                self._data["items"].append(game)
                self.__game_ids.add(game["id"])
                self._items.append(CollectionBoardGame(game))
        except KeyError:
            raise BoardGameGeekError("invalid game data")

    def __getitem__(self, item):
        return self._items.__getitem__(item)

    def __str__(self):
        return "{}'s collection, {} items".format(self.owner, len(self))

    def __repr__(self):
        return "Collection: (owner: {}, items: {})".format(self.owner, len(self))

    def __len__(self):
        return len(self._data["items"])

    @property
    def owner(self):
        """
        Return the collection's owner

        :returns: the collection's owner
        :rtype: str
        """
        return self._data.get("owner")

    @property
    def items(self):
        """
        Returns the items in the collection

        :returns: the items in the collection
        :rtype: list of :py:class:`boardgamegeek.games.CollectionBoardGame`
        """
        return self._items

    def __iter__(self):
        for item in self._data["items"]:
            yield CollectionBoardGame(item)
