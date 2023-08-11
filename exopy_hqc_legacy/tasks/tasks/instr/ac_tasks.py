# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task to set the parameters of AC sources..

"""
import time
import numbers

from atom.api import (Float, Value, Str, Int, Bool, set_default, Enum, Tuple)

from exopy.tasks.api import (InstrumentTask, TaskInterface,
                            InterfaceableTaskMixin, validators)

class SetACCurrentWaveform(InterfaceableTaskMixin, InstrumentTask):
    """Sets an AC current waveform to the specified parameters.

    """

    #: Type of waveform to be generated
    waveform_function = Str().tag(pref=True)

    #: Frequency for the waveform
    waveform_freq = Str('1.111e3').tag(
                    pref=True, 
                    feval=validators.SkipLoop(types=numbers.Real)
                    )

    #: Amplitude for the source current (dynamically evaluated)
    waveform_ampl = Str('1.0e-3').tag(
                              pref=True, 
                              feval=validators.SkipLoop(types=numbers.Real)
                              )

    #: Compliance for the source current (dynamically evaluated)
    compliance_V = Str('5.0').tag(
                              pref=True, 
                              feval=validators.SkipLoop(types=numbers.Real)
                              )

    #: Offset for the source current
    waveform_offset = Str('0.0').tag(
                              pref=True, 
                              feval=validators.SkipLoop(types=numbers.Real)
                              )

    #: Duty cycle for square and ramp waves
    waveform_duty = Float(1.0).tag(pref=True)

    #: Waveform finite boolean
    waveform_finite = Bool(False).tag(pref=True)

    #: Waveform finite cycles
    waveform_cycles = Str('1.0').tag(
                              pref=True, 
                              feval=validators.SkipLoop(types=numbers.Real)
                              )

    parallel = set_default({'activated': True, 'pool': 'instr'})
    database_entries = set_default({'current': 0.01})

    def i_perform(self, value=None):
        """Default interface.

        """
        if self.driver.owner != self.name:
            self.driver.owner = self.name
            if hasattr(self.driver, 'function') and\
                    self.driver.function != 'CURR':
                msg = ('Instrument assigned to task {} is not configured to '
                       'output a current')
                raise ValueError(msg.format(self.name))

        freq=self.format_and_eval_string(self.waveform_freq)
        ampl=self.format_and_eval_string(self.waveform_ampl)
        compl=self.format_and_eval_string(self.compliance_V)
        offset=self.format_and_eval_string(self.waveform_offset)
        cycles=self.format_and_eval_string(self.waveform_cycles)

        self.driver.set_ac_waveform(self.waveform_function,
                                    freq,
                                    ampl,
                                    offset,
                                    self.waveform_duty,
                                    self.waveform_finite,
                                    cycles)
        self.driver.current_compliance=compl

class SetACOutputTask(InterfaceableTaskMixin, InstrumentTask):
    """Set an AC output to the specified value: ON or OFF

    """
    #: Target value for the source output
    switch = Str("'OFF'").tag(pref=True, feval=validators.SkipLoop())

    database_entries = set_default({'output': "'OFF'"})

    def i_perform(self, switch=None):
        """Default interface.

        """
        if self.switch == "'ON'":
            self.driver.set_ac_output(True)
            self.write_in_database('output', "'ON'")

        elif self.switch == "'OFF'":
            self.driver.set_ac_output(False)
            self.write_in_database('output', "'OFF'")
