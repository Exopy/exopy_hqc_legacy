# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task to send parameters to the lock-in.

"""
from time import sleep
import numbers
from inspect import cleandoc

from atom.api import (set_default)

from exopy.tasks.api import InstrumentTask, validators

class SetBaseStateTask(InstrumentTask):
    """Function to turn off all instrument features

    """

    def perform(self):
        """Set the specified frequency.

        """
        self.driver.basestate_instr()
