# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2021 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tasks to set the parameters of microwave sources..

"""
import numbers

from atom.api import (Str, Bool, set_default, Enum)

from exopy.tasks.api import (InstrumentTask, InterfaceableTaskMixin,
                            validators)

CONVERSION_FACTORS = {'GHz': {'Hz': 1e9, 'kHz': 1e6, 'MHz': 1e3, 'GHz': 1},
                      'MHz': {'Hz': 1e6, 'kHz': 1e3, 'MHz': 1, 'GHz': 1e-3},
                      'kHz': {'Hz': 1e3, 'kHz': 1, 'MHz': 1e-3, 'GHz': 1e-6},
                      'Hz': {'Hz': 1, 'kHz': 1e-3, 'MHz': 1e-6, 'GHz': 1e-9},
                      'Deg': {'Rad': 0.017453292519943295, 'Deg': 1},
                      'Rad': {'Rad': 1, 'Deg': 57.29577951308232}}


LOOP_REAL = validators.SkipLoop(types=numbers.Real)


class SetRFFrequencyTask(InterfaceableTaskMixin, InstrumentTask):
    """Set the frequency of the signal delivered by a RF source.

    """
    # Target frequency (dynamically evaluated)
    frequency = Str().tag(pref=True, feval=LOOP_REAL)

    # Unit of the frequency
    unit = Enum('GHz', 'MHz', 'kHz', 'Hz').tag(pref=True)

    # Whether to start the source if its output is off.
    auto_start = Bool(False).tag(pref=True)

    database_entries = set_default({'frequency': 1.0, 'unit': 'GHz'})

    def check(self, *args, **kwargs):
        """Add the unit into the database.

        """
        test, traceback = super(SetRFFrequencyTask, self).check(*args,
                                                                **kwargs)
        self.write_in_database('unit', self.unit)

        return test, traceback

    def i_perform(self, frequency=None):
        """Default interface for simple sources.

        """
        if self.auto_start:
            self.driver.output = 'On'

        if frequency is None:
            frequency = self.format_and_eval_string(self.frequency)

        self.driver.frequency_unit = self.unit
        self.driver.frequency = frequency
        self.write_in_database('frequency', frequency)

    def convert(self, frequency, unit):
        """ Convert a frequency to the given unit.

        Parameters
        ----------
        frequency : float
            Frequency expressed in the task unit

        unit : {'Hz', 'kHz', 'MHz', 'GHz'}
            Unit in which to express the result

        Returns
        -------
        converted_frequency : float

        """
        return frequency*CONVERSION_FACTORS[self.unit][unit]


class SetRFPowerTask(InterfaceableTaskMixin, InstrumentTask):
    """Set the power of the signal delivered by the source.

    """
    # Target power (dynamically evaluated)
    power = Str().tag(pref=True, feval=LOOP_REAL)

    # Whether to start the source if its output is off.
    auto_start = Bool(False).tag(pref=True)

    database_entries = set_default({'power': -10})

    def i_perform(self, power=None):
        """

        """
        if self.auto_start:
            self.driver.output = 'On'

        if power is None:
            power = self.format_and_eval_string(self.power)

        self.driver.power = power
        self.write_in_database('power', power)


class SetRFOnOffTask(InterfaceableTaskMixin, InstrumentTask):
    """Switch on/off the output of the source.

    """
    # Desired state of the output, runtime value can be 0 or 1.
    switch = Str("'OFF'").tag(pref=True, feval=validators.SkipLoop())

    database_entries = set_default({'output': 0})

    def check(self, *args, **kwargs):
        """Validate the value of the of the switch.

        """
        test, traceback = super(SetRFOnOffTask, self).check(*args, **kwargs)

        if test and self.switch:
            try:
                switch = self.format_and_eval_string(self.switch)
            except Exception:
                return False, traceback

            if switch not in ("OFF", "ON", 0, 1):
                test = False
                traceback[self.get_error_path() + '-switch'] =\
                    '{} is not an acceptable value.'.format(self.switch)

        return test, traceback

    def i_perform(self, switch=None):
        """Default interface behavior.

        """
        if switch is None:
            switch = self.format_and_eval_string(self.switch)

        if switch == "ON" or switch == 1:
            self.driver.output = 'On'
            self.write_in_database('output', 1)
        else:
            self.driver.output = 'Off'
            self.write_in_database('output', 0)


class SetPulseModulationTask(InterfaceableTaskMixin, InstrumentTask):
    """Switch on/off the pulse modulation of the source.

    """

    # Source for mod
    source = Enum('', 'PulseGen', 'Ext', 'Random').tag(pref=True)

    # Desired state of the output, runtime value can be 0 or 1.
    switch = Str('Off').tag(pref=True, feval=validators.SkipLoop())

    # Internal pulse generator width
    pulse_width = Str('1.0').tag(pref=True)

    # Internal pulse generator period
    pulse_period = Str('1.0').tag(pref=True)

    database_entries = set_default({'pm_state': 0})

    def check(self, *args, **kwargs):
        """Validate the value of the switch.

        """
        test, traceback = super(SetPulseModulationTask, self).check(*args,
                                                                    **kwargs)

        if test and self.switch:
            try:
                switch = self.format_and_eval_string(self.switch)
                pulse_width = self.format_and_eval_string(self.pulse_width)
                pulse_period = self.format_and_eval_string(self.pulse_period)
            except Exception:
                return False, traceback

            if switch not in ('Off', 'On', 0, 1):
                test = False
                traceback[self.get_error_path() + '-switch'] =\
                    '{} is not an acceptable value.'.format(self.switch)

        return test, traceback

    def i_perform(self, switch=None):
        """Default interface behavior.

        """
        if switch is None:
            switch = self.format_and_eval_string(self.switch)

        if self.source:
            if self.source != self.driver.pm_source:
                if self.driver.pm_state:
                    self.driver.pm_state = 'Off'
                self.driver.pm_source = self.source
            if self.source == 'PulseGen':
                pulse_width = self.format_and_eval_string(self.pulse_width)
                pulse_period = self.format_and_eval_string(self.pulse_period)
                self.driver.pulse_width  = pulse_width
                self.driver.pulse_period = pulse_period

        if switch == 'On' or switch == 1:
            self.driver.pm_state = 'On'
            self.write_in_database('pm_state', 1)
        else:
            self.driver.pm_state = 'Off'
            self.driver.video_state = 'On'
            self.write_in_database('pm_state', 0)
            

class SetRFPhaseTask(InterfaceableTaskMixin, InstrumentTask):
    """Set the frequency of the signal delivered by a RF source.

    """
    # Target frequency (dynamically evaluated)
    phase = Str().tag(pref=True, feval=LOOP_REAL)

    # Unit of the frequency
    unit = Enum('Deg', 'Rad').tag(pref=True)

    # Whether to start the source if its output is off.
    auto_start = Bool(False).tag(pref=True)

    database_entries = set_default({'phase': 0.0, 'unit': 'Deg'})

    def check(self, *args, **kwargs):
        """Add the unit into the database.

        """
        test, traceback = super(SetRFPhaseTask, self).check(*args,
                                                            **kwargs)
        self.write_in_database('unit', self.unit)

        return test, traceback

    def i_perform(self, phase=None):
        """Default interface for simple sources.

        """
        if self.auto_start:
            self.driver.output = 'On'

        if phase is None:
            phase = self.format_and_eval_string(self.phase)

        self.driver.phase_unit = self.unit
        self.driver.phase = phase
        self.write_in_database('phase', phase)

    def convert(self, phase, unit):
        """ Convert a phase to the given unit.

        Parameters
        ----------
        frequency : float
            phase expressed in the task unit

        unit : {'Deg', 'Rad'}
            Unit in which to express the result

        Returns
        -------
        converted_phase : float

        """
        return phase*CONVERSION_FACTORS[self.unit][unit]
        