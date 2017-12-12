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

from atom.api import (Unicode, Float, Bool, set_default)

from exopy.tasks.api import InstrumentTask, validators


class ApplyMagFieldTask(InstrumentTask):
    """Use a supraconducting magnet to apply a magnetic field. Parallel task.

    """
    # Target magnetic field (dynamically evaluated)
    field = Unicode().tag(pref=True,
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

    def set_supervision(self, target, sweep_span, rate):
        """Wait for a field sweep, listening for a stop command
        Check the target field is reached in the end.
        When a stop is recieved, update task parameters to stop.

        target : float
            Target field in T

        sweep_span : float
            Span of the magnetic field sweep in T

        rate : float
            Sweep rate in T/min

        """
        wait = 60 * sweep_span / rate
        wait_step = 10
        time = 0
        while time < wait and not self.root.should_stop.is_set():
            sleep(wait_step)
            time += wait_step
            print(time)
        print('Wait over. Flag status %s' % self.root.should_stop.is_set())
        if self.root.should_stop.is_set():
            # update all the parameters to stop here:
            print('stopping at %s' % self.driver.out_field)
            self.driver.out_field = self.driver.out_field
            self.auto_stop_heater = False
            return False

        self.driver.check_success(target, time)
        return True

    def perform(self, target_value=None):
        """Apply the specified magnetic field.

        """
        # make ready
        if (self.driver.owner != self.name or
                not self.driver.check_connection()):
            self.driver.owner = self.name
            self.driver.make_ready()

        if target_value is None:
            target_value = self.format_and_eval_string(self.field)

        (sw_needed, heater_off) = self.driver.evaluate_state(target_value)
        if sw_needed:
            # turn heater on
            if heater_off:
                target, sw_span, rate = self.driver.prepare_heater_on()
                if self.set_supervision(target, sw_span, rate):
                    self.driver.heater_on()
                else:
                    pass

            # set the magnetic field
            target, sw_span, rate = self.driver.go_to_field(target_value, self.rate)
            self.set_supervision(target, sw_span, rate)

        # turn off heater
        if self.auto_stop_heater:
            target, sw_span, rate = self.driver.stop_heater(self.post_switch_wait)
            print('stop heater rate %s %s' % (rate, self.driver.fast_sweep_rate))
            self.set_supervision(target, sw_span, rate)

        self.write_in_database('field', target_value)
