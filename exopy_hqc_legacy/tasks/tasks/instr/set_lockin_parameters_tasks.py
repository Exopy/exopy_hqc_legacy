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
import logging
import numbers
from inspect import cleandoc

from atom.api import (Int, Value, Str, Float, Bool, set_default)

from exopy.tasks.api import (InstrumentTask, TaskInterface,
                            InterfaceableTaskMixin, validators)


class SetOscillatorFrequencyTask(InterfaceableTaskMixin, InstrumentTask):
    """Sets the frequency outputted by a lockin.

    """
    # Frequency (dynamically evaluated).
    frequency = Str().tag(pref=True, feval=validators.SkipLoop(types=numbers.Real))

    database_entries = set_default({'Frequency(Hz)': 137})

    def i_perform(self,value=None):
        """Set the specified frequency.

        """
        self.driver.set_osc_frequency(self.format_and_eval_string(self.frequency))

        self.write_in_database('Frequency(Hz)', self.format_and_eval_string(self.frequency))

class SetOscillatorAmplitudeTask(InstrumentTask):
    """Sets the Vrms outputted by a lockin.

    """
    # Amplitude.
    amplitude = Str().tag(pref=True)

    database_entries = set_default({'Vac(mV)': 100})

    def perform(self):
        """Set the specified amplitude.

        """
        self.driver.set_osc_amplitude(self.format_and_eval_string(self.amplitude))
        
        self.write_in_database('Vac(mV)', self.format_and_eval_string(self.amplitude))

class SetDemodHarmTask(InterfaceableTaskMixin, InstrumentTask):
    """Sets the harm for demod by a lockin.

    """
    # Harm.
    harm = Str().tag(pref=True)

    database_entries = set_default({'Harm': 1})

    def i_perform(self,value=None):
        """Set the specified amplitude.

        """
        self.driver.set_demod_harmonic(self.format_and_eval_string(self.harm))
        
        self.write_in_database('Harm', self.format_and_eval_string(self.harm))

class SetDemodPhaseTask(InterfaceableTaskMixin, InstrumentTask):
    """Sets the phase for demod by a lockin.

    """
    # Phase.
    phase = Str().tag(pref=True)

    database_entries = set_default({'Phase(deg)': 0})

    def i_perform(self,value=None):
        """Set the specified amplitude.

        """
        self.driver.set_demod_phase(self.format_and_eval_string(self.phase))
        
        self.write_in_database('Phase(deg)', self.format_and_eval_string(self.phase))


class MultiChannelOscillatorFrequencyInterface(TaskInterface):
    """Interface for multiple oscillators lockin.

    """
    #: Id of the channel to use.
    channel = Int(default=1).tag(pref=True)

    #: Reference to the driver for the channel.
    channel_driver = Value()

    def perform(self, value=None):
        """Set the specified frequency.

        """
        task = self.task
        if not self.channel_driver:
            self.channel_driver = task.driver.get_osc_channel(self.channel)
        if self.channel_driver.owner != task.name:
            self.channel_driver.owner = task.name
        task.driver=self.channel_driver
        task.i_perform(value)

class MultiChannelDemodInterface(TaskInterface):
    """Interface for multiple demodulators lockin.

    """
    #: Id of the channel to use.
    channel = Int(default=1).tag(pref=True)

    #: Reference to the driver for the channel.
    channel_driver = Value()

    def perform(self, value=None):
        """Set the specified frequency.

        """
        task = self.task
        if not self.channel_driver:
            self.channel_driver = task.driver.get_demod_channel(self.channel)
        if self.channel_driver.owner != task.name:
            self.channel_driver.owner = task.name
        task.driver=self.channel_driver
        task.i_perform(value)
