# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by EcpyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task perform measurements the SPDevices digitizers.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import numbers
import numpy as np
from atom.api import (Bool, Unicode, set_default)

from ecpy.tasks.api import InstrumentTask, validators

VAL_REAL = validators.Feval(types=numbers.Real)

VAL_INT = validators.Feval(types=numbers.Integral)


class DemodSPTask(InstrumentTask):
    """Get the averaged quadratures of the signal.

    """

    # return averaged data or single shot data
    average = Bool(True).tag(pref=True)

    #: Should the acquisition on channel 1 be enabled
    ch1_enabled = Bool(True).tag(pref=True)

    #: Should the acquisition on channel 2 be enabled
    ch2_enabled = Bool(True).tag(pref=True)

    #: Should the full trace be written in the database
    ch1_trace = Bool(False).tag(pref=True)

    #: Should the full trace be written in the database
    ch2_trace = Bool(False).tag(pref=True)

    #: Frequency of the signal sent to channel 1 in MHz
    freq_1 = Unicode('50').tag(pref=True, feval=VAL_REAL)

    #: Frequency of the signal sent to channel 2 in MHz
    freq_2 = Unicode('50').tag(pref=True, feval=VAL_REAL)

    #: Time during which to acquire data after a trigger (ns).
    duration = Unicode('0').tag(pref=True, feval=VAL_REAL)

    #: Time to wait after a trigger before starting acquisition (ns).
    delay = Unicode('0').tag(pref=True, feval=VAL_REAL)

    #: Number of records to acquire (one per trig)
    records_number = Unicode('1000').tag(pref=True, feval=VAL_INT)

    database_entries = set_default({'Ch1_I': 1.0, 'Ch1_Q': 1.0,
                                    'Ch2_I': 1.0, 'Ch2_Q': 1.0,
                                    'Chc_I': 1.0, 'Chc_Q': 1.0})

    def check(self, *args, **kwargs):
        """Check that parameters make sense.

        """
        test, traceback = super(DemodSPTask, self).check(*args, **kwargs)

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

        ch1, ch2 = self.driver.get_traces(channels, duration, delay,
                                          records_number)

        if self.ch1_enabled:
            f1 = self.format_and_eval_string(self.freq_1)*1e6
            ntraces1, nsamples1 = np.shape(ch1)
            phi1 = np.linspace(0, 2*np.pi*f1*((nsamples1-1)*2e-9), nsamples1)
            c1 = np.cos(phi1)
            s1 = np.sin(phi1)
            # The mean value of cos^2 is 0.5 hence the factor 2 to get the
            # amplitude.
            Ch1_I = 2*np.mean(ch1*c1, axis=1)
            Ch1_Q = 2*np.mean(ch1*s1, axis=1)
            Ch1_I_av = Ch1_I if not self.average else np.mean(Ch1_I)
            Ch1_Q_av = Ch1_Q if not self.average else np.mean(Ch1_Q)
            self.write_in_database('Ch1_I', Ch1_I_av)
            self.write_in_database('Ch1_Q', Ch1_Q_av)

            if self.ch1_trace:
                ch1_av = ch1 if not self.average else np.mean(ch1, axis=0)
                self.write_in_database('Ch1_trace', ch1_av)

        if self.ch2_enabled:
            f2 = self.format_and_eval_string(self.freq_2)*1e6
            ntraces2, nsamples2 = np.shape(ch2)
            phi2 = np.linspace(0, 2*np.pi*f2*((nsamples2-1)*2e-9), nsamples2)
            c2 = np.cos(phi2)
            s2 = np.sin(phi2)
            # The mean value of cos^2 is 0.5 hence the factor 2 to get the
            # amplitude.
            Ch2_I = 2*np.mean(ch2*c2, axis=1)
            Ch2_Q = 2*np.mean(ch2*s2, axis=1)
            Ch2_I_av = Ch2_I if not self.average else np.mean(Ch2_I)
            Ch2_Q_av = Ch2_Q if not self.average else np.mean(Ch2_Q)
            self.write_in_database('Ch2_I', Ch2_I_av)
            self.write_in_database('Ch2_Q', Ch2_Q_av)

            if self.ch2_trace:
                ch2_av = ch2 if not self.average else np.mean(ch2, axis=0)
                self.write_in_database('Ch2_trace', ch2_av)

        if self.ch1_enabled and self.ch2_enabled:
            Ch1_c = Ch1_I + 1j*Ch1_Q
            Ch2_c = Ch2_I + 1j*Ch2_Q
            Chc_I = np.real(Ch1_c/Ch2_c)
            Chc_Q = np.imag(Ch1_c/Ch2_c)
            Chc_I_av = Chc_I if not self.average else np.mean(Chc_I)
            Chc_Q_av = Chc_Q if not self.average else np.mean(Chc_Q)
            self.write_in_database('Chc_I', Chc_I_av)
            self.write_in_database('Chc_Q', Chc_Q_av)
            if self.ch1_trace:
                samples_per_period = int(500e6/f1)
                samples_per_trace = len(ch1[0])
                Ch1_c1 = ch1*c1
                Ch1_s1 = ch1*s1
                if (samples_per_trace % samples_per_period) != 0:
                    Ch1_c1 = Ch1_c1[:,
                                    :-(samples_per_trace % samples_per_period)]
                    Ch1_s1 = Ch1_s1[:,
                                    :-(samples_per_trace % samples_per_period)]
                Ch1_c1 = Ch1_c1.reshape((records_number,
                                         samples_per_trace//samples_per_period,
                                         samples_per_period))
                Ch1_I_t = 2*np.mean(Ch1_c1, axis=2)
                Ch1_s1 = Ch1_s1.reshape((records_number,
                                         samples_per_trace//samples_per_period,
                                         samples_per_period))
                Ch1_Q_t = 2*np.mean(Ch1_s1, axis=2)

                Ch1_c_t = Ch1_I_t + 1j*Ch1_Q_t
                Ch1_c_corr = np.transpose(np.transpose(Ch1_c_t)/Ch2_c)
                if not self.average:
                    Ch1_c_corr_av = Ch1_c_corr
                else:
                    Ch1_c_corr_av = np.mean(Ch1_c_corr, axis=0)
                ChI_t_corr = np.real(Ch1_c_corr_av)
                ChQ_t_corr = np.imag(Ch1_c_corr_av)
                self.write_in_database('ChI_trace_corr', ChI_t_corr)
                self.write_in_database('ChQ_trace_corr', ChQ_t_corr)

    def _post_setattr_ch1_enabled(self, old, new):
        """Update the database entries based on the enabled channels.

        """
        # TODO: how do we add the corrected I, Q Chc_I and Chc_Q
        # to the database correctly?
        entries = {'Ch1_I': 1.0, 'Ch1_Q': 1.0, 'Chc_I': 1.0, 'Chc_Q': 1.0}
        if self.ch1_trace:
            entries['Ch1_trace'] = np.array([0, 1])
            entries['ChI_trace_corr'] = np.array([0, 1])
            entries['ChQ_trace_corr'] = np.array([0, 1])
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
        self._update_entries(new, {'Ch1_trace': np.array([0, 1]),
                                   'ChI_trace_corr': np.array([0, 1]),
                                   'ChQ_trace_corr': np.array([0, 1])})

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
