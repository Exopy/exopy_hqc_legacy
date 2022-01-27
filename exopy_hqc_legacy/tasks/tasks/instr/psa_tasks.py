# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2021 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task perform measurements with a signal analyzer.

"""
import time
import numbers
from inspect import cleandoc

import numpy as np
from atom.api import (Str, Int, set_default, Enum)

from exopy.tasks.api import InstrumentTask, validators


class PSAGetTrace(InstrumentTask):
    """ Get the trace displayed on the Power Spectrum Analyzer.
    """
    mode  = Enum('SA').tag(pref=True)

    trace = Int(1).tag(pref=True)
    
    database_entries = set_default({'psa_config': '',
                                    'Freq': np.array([1.0]),
                                    'Trace1':np.array([1.0])})

    def perform(self):
        """Get the specified trace from the instrument.
        """
        if self.driver.owner != self.name:
            self.driver.owner = self.name

        sweep_modes = {'SA': 'Spectrum Analyzer',
                       'SPEC': 'Basic Spectrum Analyzer',
                       'WAV': 'Waveform'}

        d = self.driver
        header = cleandoc('''Start freq {}, Stop freq {}, Span freq {},
                          Center freq {}, Average number {}, Resolution
                          Bandwidth {}, Video Bandwidth {}, Number of points
                          {}, Mode {}''')
        psa_config = header.format(d.start_frequency_SA, d.stop_frequency_SA,
                                    d.span_frequency, d.center_frequency,
                                    d.average_count_SA, d.RBW, d.VBW_SA,
                                    d.sweep_points_SA,
                                    sweep_modes[self.driver.mode])
        self.write_in_database('psa_config', psa_config)
        
        alldata = self.driver.read_data(self.trace)
        if self.mode == 'SA':
            self.write_in_database('Freq', alldata['Frequency'])
            self.write_in_database('Trace{}'.format(self.trace),
                                                 alldata['SAdata'])

    def _post_setattr(self, old, new):
        """Update the database based on the task.

        """
        if self.mode == 'SA':
            entries = {}
            entries['psa_config'] = ''
            entries['Freq'] = np.array([1.0])
            entries['Trace{}'.format(self.trace)] = np.array([0.0])
            self.database_entries = entries

class PSASweepTask(InstrumentTask):
    """Measure over the specified sweep either on the frequency or
    other things.

    Wait for any parallel operation before execution.

    """

    mode  = Enum('SA').tag(pref=True)

    trace = Int(1).tag(pref=True)
    
    database_entries = set_default({'psa_config': '',
                                    'Freq': np.array([1.0]),
                                    'Trace1':np.array([1.0])})

    wait = set_default({'activated': True, 'wait': ['instr']})

    def perform(self):
        """Starts acquisition and gets the specified trace from the instrument.
        """
        if self.driver.owner != self.name:
            self.driver.owner = self.name

        waiting_time = self.driver.sweep_time
        if self.mode == 'SA':
            if self.driver.average_count_SA>0:
                waiting_time=waiting_time*self.driver.average_count_SA

        start_time = time.time()
        refresh_time = 5
        self.driver.single_trace_measurement()
        while True:
            remaining_time = (waiting_time -
                              (time.time() - start_time))
            if remaining_time < 0:
                break
            time.sleep(min(refresh_time, remaining_time))
            if self.root.should_stop.is_set():
                return

        is_done = self.driver.check_operation_completion()
        while not is_done:
            time.sleep(refresh_time)
            is_done = self.driver.check_operation_completion()
            if self.root.should_stop.is_set():
                return

        sweep_modes = {'SA': 'Spectrum Analyzer',
                       'SPEC': 'Basic Spectrum Analyzer',
                       'WAV': 'Waveform'}

        d = self.driver
        header = cleandoc('''Start freq {}, Stop freq {}, Span freq {},
                          Center freq {}, Average number {}, Resolution
                          Bandwidth {}, Video Bandwidth {}, Number of points
                          {}, Mode {}''')
        psa_config = header.format(d.start_frequency_SA, d.stop_frequency_SA,
                                    d.span_frequency, d.center_frequency,
                                    d.average_count_SA, d.RBW, d.VBW_SA,
                                    d.sweep_points_SA,
                                    sweep_modes[self.driver.mode])
        self.write_in_database('psa_config', psa_config)

        if is_done:
            alldata = self.driver.read_data(self.trace)
            if self.mode == 'SA':
                self.write_in_database('Freq', alldata['Frequency'])
                self.write_in_database('Trace{}'.format(self.trace),
                                                     alldata['SAdata']) 

    def _post_setattr(self, old, new):
        """Update the database based on the task.

        """
        if self.mode == 'SA':
            entries = {}
            entries['psa_config'] = ''
            entries['Freq'] = np.array([1.0])
            entries['Trace{}'.format(self.trace)] = np.array([0.0])
            self.database_entries = entries

EMPTY_REAL = validators.SkipEmpty(types=numbers.Real)

EMPTY_INT = validators.SkipEmpty(types=numbers.Integral)

class PSASetParam(InstrumentTask):
    """ Set important parameters of the Power Spectrum Analyzer.
    """
    trace = Int(1).tag(pref=True)

    mode_freq = Enum('Start/Stop', 'Center/Span').tag(pref=True)

    start_freq = Str().tag(pref=True, feval=EMPTY_REAL)

    end_freq = Str().tag(pref=True, feval=EMPTY_REAL)

    center_freq = Str().tag(pref=True, feval=EMPTY_REAL)

    span_freq = Str().tag(pref=True, feval=EMPTY_REAL)

    sweep_points = Str().tag(pref=True, feval=EMPTY_INT)

    average_nb = Str().tag(pref=True, feval=EMPTY_INT)

    resolution_bandwidth = Str().tag(pref=True, feval=EMPTY_REAL)

    video_bandwidth = Str().tag(pref=True, feval=EMPTY_REAL)

    database_entries = set_default({'psa_config': ''})

    def perform(self):
        """Set the specified parameters.
        """
        if self.driver.owner != self.name:
            self.driver.owner = self.name

        if self.mode_freq == 'Start/Stop':
            if self.start_freq:
                self.driver.start_frequency_SA = \
                    self.format_and_eval_string(self.start_freq)

            if self.end_freq:
                self.driver.stop_frequency_SA = \
                    self.format_and_eval_string(self.end_freq)

            # start_freq is set again in case the former value of stop
            # prevented to do it
            if self.start_freq:
                self.driver.start_frequency_SA = \
                    self.format_and_eval_string(self.start_freq)
        else:
            if self.center_freq:
                self.driver.center_frequency = \
                    self.format_and_eval_string(self.center_freq)

            if self.span_freq:
                self.driver.span_frequency = \
                    self.format_and_eval_string(self.span_freq)

            # center_freq is set again in case the former value of span
            # prevented to do it
            if self.center_freq:
                self.driver.center_frequency = \
                    self.format_and_eval_string(self.center_freq)

        if self.sweep_points:
            self.driver.sweep_points_SA = \
                self.format_and_eval_string(self.sweep_points)

        if self.average_nb:
            if self.format_and_eval_string(self.average_nb)>1:
                self.driver.average_state_SA = 'ON'
            else:
                self.driver.average_state_SA = 'OFF'
            self.driver.average_count_SA = \
                self.format_and_eval_string(self.average_nb)

        if self.resolution_bandwidth:
            self.driver.RBW = \
                self.format_and_eval_string(self.resolution_bandwidth)

        if self.video_bandwidth:
            self.driver.VBW_SA = \
                self.format_and_eval_string(self.video_bandwidth)

        sweep_modes = {'SA': 'Spectrum Analyzer',
                       'SPEC': 'Basic Spectrum Analyzer',
                       'WAV': 'Waveform'}

        sweep_modes = {'SA': 'Spectrum Analyzer',
                       'SPEC': 'Basic Spectrum Analyzer',
                       'WAV': 'Waveform'}

        d = self.driver
        header = cleandoc('''Start freq {}, Stop freq {}, Span freq {},
                          Center freq {}, Average number {}, Resolution
                          Bandwidth {}, Video Bandwidth {}, Number of points
                          {}, Mode {}''')
        psa_config = header.format(d.start_frequency_SA, d.stop_frequency_SA,
                                    d.span_frequency, d.center_frequency,
                                    d.average_count_SA, d.RBW, d.VBW_SA,
                                    d.sweep_points_SA,
                                    sweep_modes[self.driver.mode])
        self.write_in_database('psa_config', psa_config)

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(PSASetParam, self).check(*args, **kwargs)

        err_path = self.get_error_path()

        if kwargs.get('test_instr'):
            if (self.start_freq or 
                self.stop_freq or
                self.average_nb or
                self.video_bandwidth):
                if self.driver.mode != 'SA':
                    test = False
                    traceback[err_path] = 'PSA is not in Spectrum Analyzer mode'

        return test, traceback
        