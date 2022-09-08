# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2021 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tasks to operate on numpy.arrays.

"""
import numpy as np
import numbers

from atom.api import (Enum, Bool, Str, set_default, Float, Int)
from scipy.interpolate import splrep, sproot, splev
from scipy.optimize import curve_fit, leastsq
import scipy.ndimage.filters as flt
import matplotlib.pyplot as plt

import logging
from exopy.tasks.api import SimpleTask, InterfaceableTaskMixin, TaskInterface
from exopy.tasks.api import validators

ARR_VAL = validators.Feval(types=np.ndarray)


class FitSineTask(SimpleTask):
    """ Fit an array from the database to a cosine
        at a given freq.

    """
    #: Name of the targets in the database.
    time_array_in = Str().tag(pref=True, feval=ARR_VAL)
    val_array_in = Str().tag(pref=True, feval=ARR_VAL)

    #: Given parameters.
    freq = Str('').tag(
                    pref=True, 
                    feval=validators.SkipLoop(types=numbers.Real)
                    )
    tol_freq = Str('').tag(
                    pref=True, 
                    feval=validators.SkipLoop(types=numbers.Real)
                    )

    wait = set_default({'activated': True})  # Wait on all pools by default.

    database_entries = set_default({'freq_value': 1.0 , 'ampl_value': 1.0, 'phase_value': 1.0,
                                    'offset_value': 1.0, 'res_value': 1.0, 'fit_err': 0.0,
                                    'fitted_array': np.array([1.0])})

    def perform(self):
        t = self.format_and_eval_string(self.time_array_in)
        v = self.format_and_eval_string(self.val_array_in)
        freq = self.format_and_eval_string(self.freq)
        tol_freq = self.format_and_eval_string(self.tol_freq)

        guess_ampl = find_ampl(t,v,freq)
        guess_phase = find_phasepoint(t,v,freq)

        try:
            log = logging.getLogger(__name__)
            msg = ('Fit starts with {}, {}')
            log.warning(msg.format(guess_ampl, guess_phase))
            popt, fit_err = fit_mod(t,v,freq,tol_freq,guess_ampl,guess_phase)
        except:
            popt = [1e9,1e9,1e9,1e9]
            fit_err = 100

        self.write_in_database('res_value', np.sqrt((v-mod_funct(t, *popt))**2))
        self.write_in_database('fit_err', fit_err)
        self.write_in_database('phase_value', popt[0])
        self.write_in_database('freq_value', popt[1])
        self.write_in_database('ampl_value', popt[2])
        self.write_in_database('offset_value', popt[3])
        self.write_in_database('fitted_array', mod_funct(t, *popt))

        if fit_err > 1:
            log = logging.getLogger(__name__)
            msg = ('Fit sine has abnormally high fit error,'
                   'phase fit = {} rad, relative error = {}')
            log.warning(msg.format(round(popt[0], 3), round(fit_err, 2)))

class FitCosAndSinTask(SimpleTask):
    """ Fit an array from the database to a cos and sine
        at a given freq and phase.

    """
    #: Name of the targets in the database.
    time_array_in = Str().tag(pref=True, feval=ARR_VAL)
    val_array_in = Str().tag(pref=True, feval=ARR_VAL)

    #: Given parameters.
    freq = Str('').tag(
                    pref=True, 
                    feval=validators.SkipLoop(types=numbers.Real)
                    )
    tol_freq = Str('').tag(
                    pref=True, 
                    feval=validators.SkipLoop(types=numbers.Real)
                    )
    phase = Str('').tag(
                    pref=True, 
                    feval=validators.SkipLoop(types=numbers.Real)
                    )

    wait = set_default({'activated': True})  # Wait on all pools by default.

    database_entries = set_default({'ampl_cos_value': 1.0,
                                    'ampl_sin_value': 1.0,
                                    'freq_value': 1.0,
                                    'offset_value': 1.0,
                                    'res_value': 1.0,
                                    'fit_err': 0.0,
                                    'fitted_array': np.array([1.0])})

    def perform(self):
        t = self.format_and_eval_string(self.time_array_in)
        v = self.format_and_eval_string(self.val_array_in)
        freq = self.format_and_eval_string(self.freq)
        tol_freq = self.format_and_eval_string(self.tol_freq)
        phase = self.format_and_eval_string(self.phase)

        guess_ampl = find_ampl(t,v,freq)
        popt, fit_err = fit_knownphase(t,v,freq,tol_freq,phase,guess_ampl)

        try:
            popt, fit_err = fit_knownphase(t,v,freq,tol_freq,phase,guess_ampl)
        except:
            popt = [1e9,1e9,1e9,1e9,1e9]
            fit_err = 100

        self.write_in_database('res_value', np.sqrt((v-cossin_funct(t, phase, *popt))**2))
        self.write_in_database('fit_err', fit_err)
        self.write_in_database('freq_value', popt[0])
        self.write_in_database('ampl_cos_value', popt[1])
        self.write_in_database('ampl_sin_value', popt[2])
        self.write_in_database('offset_value', popt[3])
        self.write_in_database('fitted_array', cossin_funct(t, phase, *popt))


def find_phasepoint(t,v,freq):
    '''
    Inputs
    ------
    t:time array
    v:values array
    freq:to allow to search for 1 period

    Outputs:
    --------
    guessed phase

    '''
    period_idx=np.searchsorted(t-t[0],1/(freq))
    max_idx=np.argmax(v[:period_idx+1])
    
    return np.mod(-2*np.pi*t[max_idx]*freq+np.pi,2*np.pi)-np.pi


def find_ampl(t,v,freq):
    '''
    Inputs
    ------
    t:time array
    v:values array
    freq:to allow to search for 1 period

    Outputs:
    --------
    guessed phase

    '''
    
    return np.sqrt(2*np.mean((v-np.mean(v))**2))


def mod_funct(t, ph, freq, amp, off):
    return amp*np.cos(2*np.pi*freq*t+ph)+off

def cossin_funct(t, ph, freq, amp_cos, amp_sin, off):
    return amp_cos*np.cos(2*np.pi*freq*t+ph)+amp_sin*np.sin(2*np.pi*freq*t+ph)+off

def fit_mod(t,v,freq,tol_freq,guess_ampl,guess_phase):

    guess_off=np.mean(v)
    popt, pcov = curve_fit(mod_funct, t, v, p0=[guess_phase, freq, guess_ampl, guess_off], 
        bounds=([-np.inf, freq-tol_freq, 0, -np.inf],[np.inf, freq+tol_freq, np.inf, np.inf])
        )
    popt[0]=np.mod(popt[0]+np.pi,2*np.pi)-np.pi
    fit_error = 100*np.sqrt(pcov[0, 0])/(2*np.pi)

    return popt, fit_error

def fit_knownphase(t,v,freq,tol_freq,phase,guess_ampl):

    guess_off=np.mean(v)
    popt, pcov = curve_fit(lambda x, popt0, popt1, popt2, popt3: cossin_funct(x, phase, popt0, popt1, popt2, popt3),
        t, v, p0=[freq, guess_ampl/np.sqrt(2), guess_ampl/np.sqrt(2), guess_off], 
        bounds=([freq-tol_freq, -np.inf, -np.inf, -np.inf],[freq+tol_freq, np.inf, np.inf, np.inf])
        )
    fit_error = 50*np.sqrt(pcov[2, 2])+50*np.sqrt(pcov[3, 3])

    return popt, fit_error