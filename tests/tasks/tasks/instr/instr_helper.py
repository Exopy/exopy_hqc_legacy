# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Helpers to mock instruments

"""
from types import MethodType

from exopy_hqc_legacy.instruments.drivers.driver_tools import BaseInstrument


PROFILES = 'exopy.instruments.profiles'

DRIVERS = 'exopy.instruments.drivers'


class HelperMeta(type):
    """ Metaclass to make InstrHelper looks like a subclass of BaseInstrument.

    """

    def mro(cls):
        return (cls, object, BaseInstrument)


class InstrHelper(object, metaclass=HelperMeta):
    """ False driver used for testing purposes.

    Parameters
    ----------
    attrs : dict(str, list)
        Dict detailing the answers to returning when an attr is got as a list.

    callables : dict
        Dict detailing the answer to method calls either as callables or as
        list.

    """
    def __init__(self, attrs, callables):
        _attrs = {}
        for entry, val in attrs.items():
            if isinstance(val, list):
                # Storing value in reverse order to use pop on retrieving.
                _attrs[entry] = val[::-1]
            else:
                _attrs[entry] = val
        object.__setattr__(self, '_attrs', _attrs)

        # Dynamical method binding to instance.
        _calls = {}
        for entry, call in callables.items():
            if callable(call):
                call.__name__ = str(entry)
                object.__setattr__(self, entry, MethodType(call, self))
            else:
                _calls[entry] = call
        object.__setattr__(self, '_calls', _calls)

    def __getattr__(self, name):
        """Mock attribute access.

        """
        _attrs = self._attrs
        if name in _attrs:
            if isinstance(_attrs[name], list):
                attr = _attrs[name].pop()
            else:
                attr = _attrs[name]
            if isinstance(attr, Exception):
                raise attr
            else:
                return attr
        elif name in self._calls:
            return lambda *args, **kwargs: self._calls[name][::-1].pop()

        else:
            raise AttributeError('{} has no attr {}'.format(self, name))

    def __setattr__(self, name, value):
        """Mock attribute setting.

        """
        _attrs = self._attrs
        if name in _attrs:
            if isinstance(_attrs[name], list):
                _attrs[name].insert(0, value)
            else:
                _attrs[name] = value

        else:
            raise AttributeError('{} has no attr {}'.format(self, name))

    def close_connection(self):
        """
        """
        pass


class InstrHelperStarter(object):
    """Dummy starter for instrument objects.

    """
    def start(self, cls, connection, settings):
        """simply create an instance.

        """
        return cls(connection, settings)

    def stop(self, instr):
        """Close the dummy connection.

        """
        instr.close_connection()

    def check_infos(self, cls, connection, settings):
        """Always validate.

        """
        return True, ''
