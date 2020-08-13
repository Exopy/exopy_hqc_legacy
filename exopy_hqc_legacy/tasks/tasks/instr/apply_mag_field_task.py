# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task to apply a magnetic field.

"""
from time import sleep
import numbers
from inspect import cleandoc

from atom.api import (Str, Float, Bool, set_default)

from exopy.tasks.api import InstrumentTask, validators
from exopy_hqc_legacy.instruments.drivers.driver_tools import InstrTimeoutError


class ApplyMagFieldTask(InstrumentTask):
    """Use a supraconducting magnet to apply a magnetic field. Parallel task.

    """
    # Target magnetic field (dynamically evaluated)
    field = Str().tag(pref=True,
                          feval=validators.SkipLoop(types=numbers.Real))

    # Rate at which to sweep the field.
    rate = Float(0.01).tag(pref=True)

    # Whether to stop the switch heater after setting the field.
    auto_stop_heater = Bool(True).tag(pref=True)

    # Time to wait before bringing the field to zero after closing the switch
    # heater.
    post_switch_wait = Float(30.0).tag(pref=True)

    parallel = set_default({'activated': True, 'pool': 'instr'})
    database_entries = set_default({'field': 0.01})

    def check_for_interruption(self):
        """Check if the user required an interruption.

        """
        return self.root.should_stop.is_set()

    def perform(self, target_value=None):
        """Apply the specified magnetic field.

        """
        # make ready
        if (self.driver.owner != self.name or
                not self.driver.check_connection()):
            self.driver.owner = self.name

        if target_value is None:
            target_value = self.format_and_eval_string(self.field)

        driver = self.driver
        normal_end = True
        # Only if driver.heater_state == 'Off' otherwise we wait for 
        # post_switch_wait no matter what
        if driver.heater_state == 'Off':
            job = driver.sweep_to_persistent_field()
            if job.wait_for_completion(self.check_for_interruption,
                                       timeout=60, refresh_time=1):
                driver.heater_state = 'On'
                sleep(self.post_switch_wait)
            else:
                return False

        if (abs(driver.read_persistent_field() - target_value) > 
            driver.output_fluctuations):
            # set the magnetic field
            job = driver.sweep_to_field(target_value, self.rate)

            try:
                normal_end = job.wait_for_completion(self.check_for_interruption,
                                                    timeout=60,
                                                    refresh_time=5)
            except InstrTimeoutError:
                # job.timeout() has been called, which stops the sweep and turn off 
                # the switch heater
                self.write_in_database('field', driver.read_persistent_field())
                # fail the measurement
                self.root.should_stop.set()
                raise ValueError(cleandoc('''Field source did not set the field to 
                                          {}'''.format(target_value)))

        if not normal_end:
            # this happens when a stop signal has been send to the measurement
            job.cancel()
            return

        # turn off heater if required
        if self.auto_stop_heater:
            driver.heater_state = 'Off'
            sleep(self.post_switch_wait)
            # sweep down to zero at the fast sweep rate
            job = driver.sweep_to_field(0, driver.fast_sweep_rate)
            job.wait_for_completion(self.check_for_interruption,
                                    timeout=60, refresh_time=1)

        self.write_in_database('field', target_value)


class ApplyMagFieldAndDropTask(InstrumentTask):
    """Use a supraconducting magnet to apply a magnetic field. Parallel task.

    """
    # Target magnetic field (dynamically evaluated)
    field = Str().tag(pref=True,
                          feval=validators.SkipLoop(types=numbers.Real))

    # Rate at which to sweep the field.
    rate = Float(0.01).tag(pref=True)

    parallel = set_default({'activated': True, 'pool': 'instr'})
    database_entries = set_default({'field': 0.01})

    def check_for_interruption(self):
        """Check if the user required an interruption.

        """
        return self.root.should_stop.is_set()

    def perform(self, target_value=None):
        """Apply the specified magnetic field.

        """
        # make ready
        if (self.driver.owner != self.name or
                not self.driver.check_connection()):
            self.driver.owner = self.name

        driver = self.driver
        if driver.heater_state == 'Off':
            raise ValueError(cleandoc(''' Switch heater must be on'''))
            
        if target_value is None:
            target_value = self.format_and_eval_string(self.field)

        driver.field_sweep_rate = self.rate
        driver.target_field = target_value
        driver.activity = 'To set point'

        self.write_in_database('field', target_value)
