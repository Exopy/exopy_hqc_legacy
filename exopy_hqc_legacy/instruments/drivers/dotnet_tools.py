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

from .driver_tools import BaseInstrument

class DotNetInstrument(BaseInstrument):
    """ A base class for all instrumensts directly calling a dotnet namespace.

    Attributes
    ----------
    library : str
        Name of the library to use to control this instrument. If it is
        under the instruments/dll directory it will be automatically
        found by the DllForm.

    """

    library = ''
