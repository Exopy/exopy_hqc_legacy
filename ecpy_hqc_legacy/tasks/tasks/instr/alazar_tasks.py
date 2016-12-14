# -*- coding: utf-8 -*-
# =============================================================================
# module : alazar_tasks.py
# author : Benjamin Huard & Sébastien Jezouin
# license : MIT license
# =============================================================================
"""

"""

from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import numpy as np
from atom.api import (Str, Bool, Unicode, set_default)

from inspect import cleandoc

from ecpy.tasks.api import InstrumentTask, validators
import numbers

VAL_REAL = validators.Feval(types=numbers.Real)
VAL_INT = validators.Feval(types=numbers.Integral)

class DemodTrajAlazarTask(InstrumentTask):
    """ Get the raw or averaged quadratures of the signal.
        Can also get raw or averaged traces of the signal.
    """
    freq = Str('40').tag(pref=True)

    freqB = Str('40').tag(pref=True)

    timeaftertrig = Str('0').tag(pref=True)

    timeaftertrigB = Str('0').tag(pref=True)

    timestep = Str('0').tag(pref=True)

    timestepB = Str('0').tag(pref=True)

    tracetimeaftertrig = Str('0').tag(pref=True)

    tracetimeaftertrigB = Str('0').tag(pref=True)

    duration = Str('1000').tag(pref=True)

    durationB = Str('0').tag(pref=True)

    traceduration = Str('0').tag(pref=True)

    tracedurationB = Str('0').tag(pref=True)

    tracesbuffer = Str('20').tag(pref=True)

    tracesnumber = Str('1000').tag(pref=True)

    average = Bool(True).tag(pref=True)

    IQtracemode = Bool(False).tag(pref=True)
    driver_list = ['Alazar935x']

    database_entries = set_default({'Demod': {}, 'Trace': {}})

    def format_string(self, string, factor, n):
        s = int(self.format_and_eval_string(string))
        if isinstance(s, list) or isinstance(s, tuple) or isinstance(s, np.ndarray):
            return [elem*factor for elem in s]
        else:
            return [s*factor]*n

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(DemodTrajAlazarTask, self).check(*args,
                                                             **kwargs)

        if (int(self.format_and_eval_string(self.tracesnumber)) %
                int(self.format_and_eval_string(self.tracesbuffer)) != 0 ):
            test = False
            traceback[self.task_path + '/' + self.name + '-get_demod'] = \
                cleandoc('''The number of traces must be an integer multiple of the number of traces per buffer.''')

        if not (int(self.format_and_eval_string(self.tracesnumber)) >= 1000):
            test = False
            traceback[self.task_path + '/' + self.name + '-get_demod'] = \
                cleandoc('''At least 1000 traces must be recorded. Please make real measurements and not noisy s***.''')

        time = self.format_string(self.timeaftertrig, 10**-9, 1)
        duration = self.format_string(self.duration, 10**-9, 1)
        timeB = self.format_string(self.timeaftertrigB, 10**-9, 1)
        durationB = self.format_string(self.durationB, 10**-9, 1)
        tracetime = self.format_string(self.tracetimeaftertrig, 10**-9, 1)
        traceduration = self.format_string(self.traceduration, 10**-9, 1)
        tracetimeB = self.format_string(self.tracetimeaftertrigB, 10**-9, 1)
        tracedurationB = self.format_string(self.tracedurationB, 10**-9, 1)

        for t, d in ((time,duration), (timeB,durationB), (tracetime,traceduration), (tracetimeB,tracedurationB)):
            if len(t) != len(d):
                test = False
                traceback[self.task_path + '/' + self.name + '-get_demod'] = \
                    cleandoc('''An equal number of "Start time after trig" and "Duration" should be given.''')
            else :
                for tt, dd in zip(t, d):
                    if not (tt >= 0 and dd >= 0) :
                           test = False
                           traceback[self.task_path + '/' + self.name + '-get_demod'] = \
                               cleandoc('''Both "Start time after trig" and "Duration" must be >= 0.''')

        if ((0 in duration) and (0 in durationB) and (0 in traceduration) and (0 in tracedurationB)):
            test = False
            traceback[self.task_path + '/' + self.name + '-get_demod'] = \
                           cleandoc('''All measurements are disabled.''')

        timestep = self.format_string(self.timestep, 10**-9, len(time))
        timestepB = self.format_string(self.timestepB, 10**-9, len(timeB))
        freq = self.format_string(self.freq, 10**6, len(time))
        freqB = self.format_string(self.freqB, 10**6, len(timeB))
        samplesPerSec = 500000000.0

        if 0 in duration:
            duration = []
            timestep = []
            freq = []
        if 0 in durationB:
            durationB = []
            timestepB = []
            freqB = []

        for d, ts in zip(duration+durationB, timestep+timestepB):
            if ts and np.mod(int(samplesPerSec*d), int(samplesPerSec*ts)):
                test = False
                traceback[self.task_path + '/' + self.name + '-get_demod'] = \
                   cleandoc('''The number of samples in "IQ time step" must divide the number of samples in "Duration".''')

        for f, ts in zip(freq+freqB, timestep+timestepB):
            if ts and np.mod(f*int(samplesPerSec*ts), samplesPerSec):
                test = False
                traceback[self.task_path + '/' + self.name + '-get_demod'] = \
                   cleandoc('''The "IQ time step" does not cover an integer number of demodulation periods.''')

        return test, traceback

    def perform(self):
        """
        """
        if not self.driver:
            self.start_driver()

        if self.driver.owner != self.name:
            self.driver.owner = self.name

        self.driver.configure_board()

        records_number = self.format_and_eval_string(self.records_number)
        delay = self.format_and_eval_string(self.delay)*1e-9
        duration = self.format_and_eval_string(self.duration)*1e-9

        channels = (self.ch1_enabled, self.ch2_enabled)
        ch1, ch2 = self.driver.get_traces(channels, duration, delay,
                                          records_number)
        if self.ch1_enabled:
            f1 = self.format_and_eval_string(self.freq_1)*1e6
            phi1 = np.linspace(0, 2*np.pi*f1*duration, len(ch1))
            c1 = np.cos(phi1)
            s1 = np.sin(phi1)
            # The mean value of cos^2 is 0.5 hence the factor 2 to get the
            # amplitude.
            self.write_in_database('Ch1_I', 2*np.mean(ch1*c1))
            self.write_in_database('Ch1_Q', 2*np.mean(ch1*s1))
            if self.ch1_trace:
                self.write_in_database('Ch1_trace', ch1)

        if self.ch2_enabled:
            f2 = self.format_and_eval_string(self.freq_2)*1e6
            phi2 = np.linspace(0, 2*np.pi*f2*duration, len(ch2))
            c2 = np.cos(phi2)
            s2 = np.sin(phi2)
            # The mean value of cos^2 is 0.5 hence the factor 2 to get the
            # amplitude.
            self.write_in_database('Ch2_I', 2*np.mean(ch2*c2))
            self.write_in_database('Ch2_Q', 2*np.mean(ch2*s2))
            if self.ch2_trace:
                self.write_in_database('Ch2_trace', ch2)

class DemodAlazarTask(InstrumentTask):
    """Get the averaged quadratures of the signal.

    """
    #: Should the acquisition on channel 1 be enabled
    ch1_enabled = Bool(True).tag(pref=True)

    #: Should the acquisition on channel 2 be enabled
    ch2_enabled = Bool(True).tag(pref=True)

    #: Should the full trace be written in the database
    ch1_trace = Bool(False).tag(pref=True)

    #: Should the full trace be written in the database
    ch2_trace = Bool(False).tag(pref=True)

    #: Frequency of the signal sent to channel 1 in MHz
    freq_1 = Unicode('20').tag(pref=True, feval=VAL_REAL)

    #: Frequency of the signal sent to channel 2 in MHz
    freq_2 = Unicode('20').tag(pref=True, feval=VAL_REAL)

    #: Time during which to acquire data after a trigger (ns).
    duration = Unicode('0').tag(pref=True, feval=VAL_REAL)

    #: Time to wait after a trigger before starting acquisition (ns).
    delay = Unicode('0').tag(pref=True, feval=VAL_REAL)

    #: Number of records to acquire (one per trig)
    records_number = Unicode('1000').tag(pref=True, feval=VAL_INT)

    database_entries = set_default({'Ch1_I': 1.0, 'Ch1_Q': 1.0,
                                    'Ch2_I': 1.0, 'Ch2_Q': 1.0})

    def check(self, *args, **kwargs):
        """Check that parameters make sense.

        """
        test, traceback = super(DemodAlazarTask, self).check(*args, **kwargs)

        if not test:
            return test, traceback

        locs = {}
        to_eval = (('duration',) + (('freq_1',) if self.ch1_enabled else ()) +
                   (('freq_2',) if self.ch2_enabled else ()))
        for n in to_eval:
            locs[n] = self.format_and_eval_string(getattr(self, n))

        p1 = locs['freq_1']*locs['duration']*1e-3 if self.ch1_enabled else 1.
        p2 = locs['freq_2']*locs['duration']*1e-3 if self.ch2_enabled else 1.
        if (not p1.is_integer() or not p2.is_integer()):
            test = False
            msg = ('The duration must be an integer times the period of the '
                   'demodulations.')
            traceback[self.get_error_path() + '-' + n] = msg

        if self.ch1_enabled and self.ch1_trace:
            phi1 = np.linspace(0, 2*np.pi*locs['freq_1']*locs['duration'], p1)
            self.write_in_database('Ch1_trace', np.sin(phi1))
        if self.ch2_enabled and self.ch2_trace:
            phi2 = np.linspace(0, 2*np.pi*locs['freq_2']*locs['duration'], p2)
            self.write_in_database('Ch2_trace', np.sin(phi2))

        return test, traceback

    def perform(self):
        """Acquire the averaged trace and compute the demodualted
        signal for both channels.

        """
        if self.driver.owner != self.name:
            self.driver.owner = self.name

            self.driver.configure_board()

        records_number = self.format_and_eval_string(self.records_number)
        delay = self.format_and_eval_string(self.delay)*1e-9
        duration = self.format_and_eval_string(self.duration)*1e-9

        channels = (self.ch1_enabled, self.ch2_enabled)
        #ch1, ch2 = self.driver.get_traces(channels, duration, delay,
        #                                  records_number)
        average = True
        timeaftertrig = duration
        recordsPerCapture = records_number
        recordsPerBuffer = 1
        ch1, ch2 = self.driver.get_traces(timeaftertrig, recordsPerCapture,
                   recordsPerBuffer, average)
        if self.ch1_enabled:
            f1 = self.format_and_eval_string(self.freq_1)*1e6
            phi1 = np.linspace(0, 2*np.pi*f1*duration, len(ch1))
            c1 = np.cos(phi1)
            s1 = np.sin(phi1)
            # The mean value of cos^2 is 0.5 hence the factor 2 to get the
            # amplitude.
            self.write_in_database('Ch1_I', 2*np.mean(ch1*c1))
            self.write_in_database('Ch1_Q', 2*np.mean(ch1*s1))
            if self.ch1_trace:
                self.write_in_database('Ch1_trace', ch1)

        if self.ch2_enabled:
            f2 = self.format_and_eval_string(self.freq_2)*1e6
            phi2 = np.linspace(0, 2*np.pi*f2*duration, len(ch2))
            c2 = np.cos(phi2)
            s2 = np.sin(phi2)
            # The mean value of cos^2 is 0.5 hence the factor 2 to get the
            # amplitude.
            self.write_in_database('Ch2_I', 2*np.mean(ch2*c2))
            self.write_in_database('Ch2_Q', 2*np.mean(ch2*s2))
            if self.ch2_trace:
                self.write_in_database('Ch2_trace', ch2)

    def _post_setattr_ch1_enabled(self, old, new):
        """Update the database entries based on the enabled channels.

        """
        entries = {'Ch1_I': 1.0, 'Ch1_Q': 1.0}
        if self.ch1_trace:
            entries['Ch1_trace'] = np.array([0, 1])
        self._update_entries(new, entries)

    def _post_setattr_ch2_enabled(self, old, new):
        """Update the database entries based on the enabled channels.

        """
        entries = {'Ch2_I': 1.0, 'Ch2_Q': 1.0}
        if self.ch2_trace:
            entries['Ch2_trace'] = np.array([0, 1])
        self._update_entries(new, entries)

    def _post_setattr_ch1_trace(self, old, new):
        """Update the database entries based on the trace setting.

        """
        if new and not self.ch1_enabled:
            return
        self._update_entries(new, {'Ch1_trace': np.array([0, 1])})

    def _post_setattr_ch2_trace(self, old, new):
        """Update the database entries based on the trace settings.

        """
        if new and not self.ch2_enabled:
            return
        self._update_entries(new, {'Ch2_trace': np.array([0, 1])})

    def _update_entries(self, new, defaults):
        """Update database entries.

        """
        entries = self.database_entries.copy()
        if new:
            entries.update(defaults)
        else:
            for e in defaults:
                if e in entries:
                    del entries[e]
        self.database_entries = entries


class TracesAlazarTask(InstrumentTask):
    """ Get the raw or averaged traces of the signal.

    """

    timeaftertrig = Str().tag(pref=True)

    tracesnumber = Str().tag(pref=True)

    tracesbuffer = Str().tag(pref=True)

    average = Bool(True).tag(pref=True)

    driver_list = ['Alazar935x']

    database_entries = set_default({'traceA': np.zeros((1, 1)),
                                    'traceB': np.zeros((1, 1))})

    def check(self, *args, **kwargs):
        """
        """
        test, traceback = super(TracesAlazarTask, self).check(*args,
                                                              **kwargs)

        if (int(self.format_and_eval_string(self.tracesnumber)) %
                int(self.format_and_eval_string(self.tracesbuffer))) != 0:
            test = False
            traceback[self.task_path + '/' + self.name + '-get_traces'] =\
                cleandoc('''The number of buffers used must be an integer.''')

        return test, traceback

    def perform(self):
        """
        """
        if not self.driver:
            self.start_driver()

        if self.driver.owner != self.name:
            self.driver.owner = self.name

        self.driver.configure_board()

        recordsPerCapture = int(max(1000,
                            int(self.format_and_eval_string(self.tracesnumber))))

        recordsPerCapture = int(self.format_and_eval_string(self.tracesnumber)) # ZL: added this line

        recordsPerBuffer = int(self.format_and_eval_string(self.tracesbuffer))

        answer = self.driver.get_traces(
            self.format_and_eval_string(self.timeaftertrig)*10**-6,
            recordsPerCapture, recordsPerBuffer, self.average
            )

        traceA, traceB = answer
        print('TRACE A SHAPE :'+str(np.shape(traceA)))
        print('TRACE B SHAPE :'+str(np.shape(traceB)))
        self.write_in_database('traceA', traceA)
        self.write_in_database('traceB', traceB)
