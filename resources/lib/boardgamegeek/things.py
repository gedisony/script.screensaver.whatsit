# coding: utf-8
"""
:mod:`boardgamegeek.things` - Generic objects
=============================================

.. module:: boardgamegeek.things
   :platform: Unix, Windows
   :synopsis: Generic objects

.. moduleauthor:: Cosmin Luță <q4break@gmail.com>

"""
from __future__ import unicode_literals

from .exceptions import BoardGameGeekError
from .utils import DictObject


class Thing(DictObject):
    """
    A thing, an object with a name and an id. Base class for various objects in the library.
    """
    def __init__(self, data):
        for i in ["id", "name"]:
            if i not in data:
                raise BoardGameGeekError("missing '{}' when trying to create a Thing".format(i))

        try:
            data["id"] = int(data["id"])
        except:
            raise BoardGameGeekError("id ({}) is not an int when trying to create a Thing".format(data["id"]))

        super(Thing, self).__init__(data)

    @property
    def name(self):
        """
        :return: name
        :rtype: str
        """
        return self._data["name"]

    @property
    def id(self):
        """
        :return: id
        :rtype: integer
        """
        return self._data["id"]

    def __repr__(self):
        return "Thing (id: {})".format(self.id)
