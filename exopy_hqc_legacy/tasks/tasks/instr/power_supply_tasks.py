# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2022 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task to deliver a current with power supply.

"""
from time import sleep
import numbers
from inspect import cleandoc
import logging

from atom.api import (Str, Float, Bool, set_default)

from exopy.tasks.api import InstrumentTask, validators
from exopy_hqc_legacy.instruments.drivers.driver_tools import InstrTimeoutError,InstrIOError

class ApplyPowerCurrentTask(InstrumentTask):
    """Use a current-controlled electromagnet to apply a magnetic field.

    """
    # Target magnetic field (dynamically evaluated)
    output_current = Str().tag(pref=True,
                          feval=validators.SkipLoop(types=numbers.Real))

    database_entries = set_default({'output_current': 0.01})

    def perform(self, target_value=None):
        """Apply the specified magnetic field.

        """
        # make ready
        if (self.driver.owner != self.name):
            self.driver.owner = self.name

        if target_value is None:
            target_value = self.format_and_eval_string(self.output_current)

        self.driver.output_current = target_value
        read_value = self.driver.output_current
        if abs(read_value-target_value)>1e-3:
            raise InstrIOError(cleandoc('''Magnet PS did not set correctly 
                                         the output current'''))

        self.write_in_database('output_current', target_value)