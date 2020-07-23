# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tasks to set the parameters of arbitrary waveform generators.

"""
import logging
import numbers
import time

from atom.api import (Float, Unicode, set_default)

from exopy.tasks.api import (InstrumentTask, validators)


class RunAWGTask(InstrumentTask):
    """ Task to set AWG run mode

    """
    #: Switch to choose the AWG run mode: on or off
    switch = Unicode('Off').tag(pref=True, feval=validators.SkipLoop())
    delay = Float(0).tag(pref=True)
    database_entries = set_default({'output': 0})

    def perform(self, switch=None):
        """Default interface behavior.

        """
        if switch is None:
            switch = self.format_and_eval_string(self.switch)
        if switch == 'On' or switch == 1:
            self.driver.send_event()
            # The delay is required when loading large sequences
            self.driver.run_awg(1, delay=delay)
            self.write_in_database('output', 1)
        elif switch == 'Event':
            time.sleep(delay)
            self.driver.send_event()
        elif switch == 'Rearm':
            print('Rearm')
            time.sleep(delay)
            success = False
            while not success:
                self.driver.send_event()
                pos = int(self.driver.ask_sequencer_pos())
                if pos == 1:
                    success = True
            time.sleep(delay)
        else:
            time.sleep(delay)
            self.driver.run_awg(0)
            self.write_in_database('output', 0)
        log = logging.getLogger(__name__)
        msg = 'AWG running state OK'
        log.debug(msg)
