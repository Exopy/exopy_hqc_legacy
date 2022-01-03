# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2022 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Base classes for instrument relying on a python API for communication.

"""
import time

from .driver_tools import BaseInstrument, InstrIOError


class PyAPIInstrument(BaseInstrument):
    """ A base class for all instruments directly calling a python API.

    Attributes
    ----------
    library : python class object
        Name of the library to use to control this instrument. If is is
        under the instruments/dll directory it will be automatically
        found by the DllForm.

    """

    library = ''
