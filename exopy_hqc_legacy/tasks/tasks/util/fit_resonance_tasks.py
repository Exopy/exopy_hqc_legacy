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
from atom.api import (Enum, Bool, Str, set_default, Float, Int)
from scipy.interpolate import splrep, sproot, splev
from scipy.optimize import curve_fit, leastsq
import scipy.ndimage.filters as flt
import matplotlib.pyplot as plt

import logging
from exopy.tasks.api import SimpleTask, InterfaceableTaskMixin, TaskInterface
from exopy.tasks.api import validators

ARR_VAL = validators.Feval(types=np.ndarray)


class FitResonanceTask(InterfaceableTaskMixin, SimpleTask):
    """ Load an array from the disc into the database.

    """
    #: Name of the target in the database.
    target_array = Str().tag(pref=True, feval=ARR_VAL)
    ref_array = Str().tag(pref=True, feval=ARR_VAL)
    use_ref = Bool(False).tag(pref=True)

    #: Kind of data to fit.
    selected_format = Str().tag(pref=True)

    wait = set_default({'activated': True})  # Wait on all pools by default.

    database_entries = set_default({'res_value': 1.0, 'fit_err': 0.0})

    def check(self, *args, **kwargs):
        """Check that the provided path and filename make sense.

        """
        test, traceback = super(FitResonanceTask, self).check(*args, **kwargs)
        err_path = self.get_error_path()

        if not test:
            return test, traceback

#        full_folder_path = self.format_string(self.folder)
#        filename = self.format_string(self.filename)
#        full_path = os.path.join(full_folder_path, filename)
#
#        if not os.path.isfile(full_path):
#            msg = ('File does not exist, be sure that your measure  will '
#                   'create it before this task is executed.')
#            traceback[err_path + '-file'] = msg

        return test, traceback


class FitVNAInterface(TaskInterface):
    """ Store the pair(s) of index/value for the resonance frequency.

    Wait for any parallel operation before execution.

    """
    #: Name of the column into which the extrema should be looked for.
    column_name_maglin = Str().tag(pref=True)
    column_name_phase = Str().tag(pref=True)
    column_name_freq = Str().tag(pref=True)

    #: Flag indicating the measurement setup. This changes the fit function
    mode = Enum('Reflection', 'Transmission', 'Lorentzian').tag(pref=True)

    array_format = ['VNA']

    def perform(self):
        """ Find resonance frequency of database array and store index/value
            pairs.

        """
        task = self.task
        use_ref = task.use_ref
        array = task.format_and_eval_string(task.target_array)
        if use_ref:
            array_ref = task.format_and_eval_string(task.ref_array)

        freq = array[self.column_name_freq]
        data_maglin = array[self.column_name_maglin]
        delay = 111

        if self.mode == 'Reflection':
            data_phase = array[self.column_name_phase]
            data_c = data_maglin*np.exp(1j*np.pi/180*data_phase)*np.exp(1j*2*np.pi*freq*delay*1e-9)
            if use_ref:
                freq_ref = array_ref[self.column_name_freq]
                data_maglin_ref = array_ref[self.column_name_maglin]
                data_phase_ref = array_ref[self.column_name_phase]
                freq_ref, data_maglin_ref, data_phase_ref = adapt_ref(freq, freq_ref, data_maglin_ref, data_phase_ref)
                data_c_ref = data_maglin_ref*np.exp(1j*np.pi/180*data_phase_ref)
                data_c = data_c/data_c_ref

        if self.mode == 'Lorentzian':
            data_error = array[self.column_name_phase]
        if self.mode == 'Reflection':
            try:
                val, fit_err = fit_complex_a_out(freq, data_c)
            except:
                val = 1e9
                fit_err = 100
        if self.mode == 'Transmission':
            try:
                print(np.shape(freq), np.shape(data_maglin))
                val, fit_err = fit_lorentzian(freq, data_maglin)
            except:
                val = 1e9
                fit_err = 100
        if self.mode == 'Lorentzian':
            try:
                val, fit_err = fit_lorentzian(freq, data_maglin, error=data_error)
            except:
                val = 1e9
                fit_err = 100

        task.write_in_database('res_value', val)
        print('freq = '+str(np.round(val*1e-9, 5)*1e9) + ', error = '+str(np.round(fit_err, 2)))
        task.write_in_database('fit_err', fit_err)
        if fit_err > 1:
            log = logging.getLogger(__name__)
            msg = ('Fit resonance has abnormally high fit error,'
                   'freq fit = {} GHz, relative error = {}')
            log.warning(msg.format(round(val*1e-9, 3), round(fit_err, 2)))

class FitAlazarInterface(TaskInterface):
    """ Store the pair(s) of index/value for the resonance frequency.

    Wait for any parallel operation before execution.

    """
    #: Name of the column into which the extrema should be looked for.
    column_name_Icor = Str().tag(pref=True)
    column_name_Qcor = Str().tag(pref=True)
    column_name_freq = Str().tag(pref=True)
    Tdelay = Str().tag(pref=True)

    #: Flag indicating the measurement setup. This changes the fit function
    mode = Enum('Reflection', 'Transmission', 'Lorentzian').tag(pref=True)

    array_format = ['Alazar']

    def perform(self):
        """ Find resonance frequency of database array and store index/value
            pairs.

        """
        task = self.task
        array = task.format_and_eval_string(task.target_array)
        if 1 == 0:
            array_ref = task.format_and_eval_string(task.ref_array)

        freq = 1e9*array[self.column_name_freq]
        Icor = array[self.column_name_Icor]
        Qcor = array[self.column_name_Qcor]
        Tdelay = float(task.format_and_eval_string(self.Tdelay))*1e-9
        data_c = (Icor + 1j*Qcor)*np.exp(1j*2*np.pi*freq*Tdelay)
        data_maglin = np.abs(data_c)

        if self.mode == 'Reflection':
            try:
                val, fit_err = fit_complex_a_out(freq, data_c)
            except:
                val = 1e9
                fit_err = 100
        if self.mode == 'Transmission':
            try:
                print(np.shape(freq), np.shape(data_maglin))
                val, fit_err = fit_lorentzian(freq, data_maglin)
            except:
                val = 1e9
                fit_err = 100
        if self.mode == 'Lorentzian':
            try:
                val, fit_err = fit_lorentzian(freq, data_maglin)
            except:
                val = 1e9
                fit_err = 100

        task.write_in_database('res_value', val)
        print('freq = '+str(np.round(val*1e-9, 5)*1e9) + ', error = '+str(np.round(fit_err, 2)))
        task.write_in_database('fit_err', fit_err)
        if fit_err > 1:
            log = logging.getLogger(__name__)
            msg = ('Fit resonance has abnormally high fit error,'
                   'freq fit = {} GHz, relative error = {}')
            log.warning(msg.format(round(val*1e-9, 3), round(fit_err, 2)))

def _find_weights(x, x_ref):
    '''
    Inputs
    ------
    x(float):x_value we want to bound by 2 x_refs values
    x_ref(array)

    Outputs:
    --------
    indices(int): indices of bounds in x_ref
    weights(list): weights of either bound

    '''
    if x>np.max(x_ref) or x<np.min(x_ref):
        raise ValueError('Searched value should be in the bound of the search array')
    i0 = np.argmin(np.abs(x_ref-x))
    x0_ref = x_ref[i0]

    if x>=x0_ref and x0_ref != np.max(x_ref):
        i1 = i0+1
        x1_ref = x_ref[i1]
    else:
        i1 = i0
        x1_ref = x0_ref
        i0 = i0-1
        x0_ref = x_ref[i0]

    delta_x = x1_ref-x0_ref
    weight_x0 = 1-(x-x0_ref)/delta_x
    weight_x1 = 1-(-x+x1_ref)/delta_x

    return(i0,i1, weight_x0, weight_x1)


def adapt_ref(x_data, x_ref, maglin_ref, phase_ref):
    '''
    If x_data and x_ref are not the same, interpolate the data_ref to match
    the data linspace.

    Inputs
    ------
    x_data(array): data to be fitter
    x_ref(array): ref support (e.g. spec frequecies)
    maglin_ref(array): data_ref
    phase_ref(array): data_ref

    Outputs:
    --------
    adapted x_ref(array), maglin_ref(array) and phase_ref(array)

    '''
    data_c_ref =  maglin_ref*np.exp(1j*np.pi/180*phase_ref)
    X = len(x_data)
    maglin_ref_adapted = np.empty(X)
    phase_ref_adapted = np.empty(X)
    for ii, x in enumerate(x_data):
        i0, i1, w0, w1 = _find_weights(x, x_ref)
        data_c_calc = data_c_ref[i0]*w0+data_c_ref[i1]*w1
        maglin_ref_adapted[ii] = np.abs(data_c_calc)
        phase_ref_adapted[ii] = 180/np.pi*np.angle(data_c_calc)
    return(x_data, maglin_ref_adapted, phase_ref_adapted)


def complex_fit(f, xData, yData, p0, weights=None, bounds=()):
    if np.isscalar(p0):
        p0 = np.array([p0])

    def residuals(params, x, y):
        if weights is not None:
            diff = weights * f(x, *params) - y
        else:
            diff = f(x, *params) - y
        flatDiff = np.zeros(diff.size * 2, dtype=np.float64)
        flatDiff[0:flatDiff.size:2] = diff.real
        flatDiff[1:flatDiff.size:2] = diff.imag
        return flatDiff

    res = leastsq(residuals, p0, args=(xData, yData), maxfev=1000,
                  ftol=1e-2, full_output=1)
    return res[0], res[1]


def complex_a_out(f, f_0, kc, ki, a_in, T):  # kc and ki are kappas/2pi
    D = f - f_0
    num = - 1j*D + (kc - ki)/2
    den = 1j*D + (kc+ki)/2
    if kc > 0 and ki > 0 and f_0 > 0:
        return num/den*a_in*np.exp(1j*D*T)
    else:
        return np.Inf


def fit_complex_a_out(f, a_out):
    f_0, kc = get_f0_reflection(f, a_out)
    kc = 10e6
    ki = 1e6
    T = 0

#    plt.close('all')
#    fig, ax = plt.subplots(3)
#    ax[0].scatter(f, np.abs(a_out))
#    ax[1].scatter(f, np.angle(a_out))
#    ax[0].plot([f_0, f_0], [min(np.abs(a_out)), max(np.abs(a_out))])
#    ax[0].plot([f_0-kc, f_0+kc], [max(np.abs(a_out)), max(np.abs(a_out))])
#    ax[2].scatter(np.real(a_out), np.imag(a_out))
#    ax[2].axis('equal')
#    plt.show()

    def aux(f, f_0, kc, ki, re_a_in, im_a_in, T):
        return complex_a_out(f, f_0, kc, ki, re_a_in + 1j*im_a_in, T)
    a_in = -a_out[0]
    popt, pcov = complex_fit(aux, f, a_out, (f_0, kc, ki, np.real(a_in),
                                             np.imag(a_in), T))
    fit_error = 100*np.sqrt(pcov[0, 0])/popt[0]

#    print(popt)

#    a_out_fit = complex_a_out(f, *popt)
#    ax[0].plot(f, np.abs(a_out_fit))
#    ax[1].plot(f, np.angle(a_out_fit))
#
    return popt[0], fit_error


def get_f0_reflection(f, a_out):
    phase = np.unwrap(np.angle(a_out))
    phase_avg = (np.min(phase)+np.max(phase))/2
    spline = splrep(f, phase-phase_avg)
    roots = sproot(spline)
    if len(roots) != 1:
        maglin = np.abs(a_out)
        f0 = f[np.argmin(maglin)]
    else:
        f0 = roots[0]

    phase_flt = flt.gaussian_filter(phase, 1)
    dphase_flt = np.diff(phase_flt)
    df = f[:-1]
    spline = splrep(df, dphase_flt-(max(dphase_flt)+min(dphase_flt))/2)
    roots = sproot(spline)
    kc = roots[-1]-roots[0]
    return f0, kc


def lorentzian(x, x0, y0, A, B):
    numerator = A
    denominator = (x - x0)**2 + B
    y = y0 + (numerator/denominator)
    return y


def fit_lorentzian(x, y, error=None):
    if error is not None:
        for ii in range(len(y)):
            if error[ii] > 1:
                y[ii] = y[ii-1]

    ymean = np.mean(y)
    ymax = np.amax(y)
    ymin = np.amin(y)
    if ymean < (ymax+ymin)/2:
        index = np.argmax(y)
#        print(index)
        y0 = ymin
    else:
        ymax = ymin
        index = np.argmin(y)
        y0 = ymax
    x0 = x[index]
    spline = splrep(x, y-(y0+ymax)/2)
    roots = sproot(spline)
    whm = roots[-1]-roots[0]

    B = whm*whm/4.0
    A = B*(ymax-y0)
    popt, pcov = curve_fit(lorentzian, x, y, (x0, y0, A, B))
    fit_error = 100*np.sqrt(pcov[0, 0])/popt[0]

#    plt.close('all')
#    fig, ax = plt.subplots()
#    ax.scatter(x, y)
#    ax.plot(x, lorentzian(x, *popt))
#    ax.plot([min(x), max(x)], [y0, y0])
#    ax.plot([min(x), max(x)], [ymax, ymax])
#    ax.plot([x0, x0], [y0, ymax])
#    plt.show()
#    print(popt)
    return popt[0], fit_error
