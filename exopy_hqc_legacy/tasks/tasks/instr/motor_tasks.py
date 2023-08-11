# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2023 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task perform measurements with motors.

"""
import numbers
import numpy as np
import time
import logging
from atom.api import (Bool, Str, Enum, Float, set_default)

from exopy.tasks.api import InstrumentTask, validators

VAL_REAL = validators.Feval(types=numbers.Real)

VAL_INT = validators.Feval(types=numbers.Integral)

class MoveAbsMotorTask(InstrumentTask):
    """Moves motor to requested angle.

    """

    #: Abs to move to
    angle_reached = Str('360.0').tag(pref=True,
                          feval=validators.SkipLoop(types=numbers.Real))

    database_entries = set_default({'angle_reached': 360.0})

    def perform(self, target_value=None):
        """Execute motion

        """
        # make ready
        if (self.driver.owner != self.name):
            self.driver.owner = self.name

        if target_value is None:
            target_value = self.format_and_eval_string(self.angle_reached)

        self.driver.move_motor_abs(target_value)
        new_angle = self.driver.get_present_abs_angle()
        self.write_in_database('angle_reached', new_angle)

class MoveRelMotorTask(InstrumentTask):
    """Moves motor by requested angle diff.

    """

    #: Pos or neg relative angle by which to move
    angle_reached = Str('0.0').tag(pref=True,
                          feval=validators.SkipLoop(types=numbers.Real))

    database_entries = set_default({'angle_reached': 360.0})

    def perform(self, target_value=None):
        """Execute motion

        """
        # make ready
        if (self.driver.owner != self.name):
            self.driver.owner = self.name

        if target_value is None:
            target_value = self.format_and_eval_string(self.angle_reached)

        self.driver.move_motor_rel(target_value)
        new_angle = self.driver.get_present_abs_angle()
        self.write_in_database('angle_reached', new_angle)

class MotorReturnAngleTask(InstrumentTask):
    """Simply read motor angular position.

    Wait for any parallel operation before execution and then wait the
    specified time before perfoming the measure.

    """
    # Time to wait before the measurement.
    wait_time = Float().tag(pref=True)

    database_entries = set_default({'angle_read': 360.0})

    wait = set_default({'activated': True, 'wait': ['instr']})

    def perform(self):
        """Wait and read the magnetic field.

        """
        
        # make ready
        if (self.driver.owner != self.name):
            self.driver.owner = self.name

        time.sleep(self.wait_time)

        new_angle = self.driver.get_present_abs_angle()
        
        self.write_in_database('angle_read', new_angle)
