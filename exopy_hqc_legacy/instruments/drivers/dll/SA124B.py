# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2017 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""This module defines drivers for Alazar using DLL Library.

:Contains:
    SA124B

Visual C++ runtime needs to be installed to be able to load the dll.

"""
import time
import ctypes
from subprocess import call

import numpy as np
import os

from ..dll_tools import DllInstrument
from ..driver_tools import InstrIOError
import sys

# to get the sa_api DLL imported, one should add th pathe C:\\Program Files\\Signal Hound\\Spike to the os environ path
pastr = "C:\Program Files\Signal Hound\Spike"
os.environ['PATH'] += ";" + pastr

sa_dll = ctypes.CDLL("sa_api.dll")

SA_TRUE  = 1
SA_FALSE = 0

#Modes
SA_IDLE      = -1
SA_SWEEPING  = 0x0
SA_REAL_TIME = 0x1
SA_IQ        = 0x2
SA_AUDIO     = 0x3
SA_TG_SWEEP  = 0x4

#Limits
SA124_MIN_FREQ       = 100.0e3
SA124_MAX_FREQ       = 13.0e9
SA_MIN_SPAN          = 1.0
SA_MAX_REF           = 20 # dBm
SA_MAX_ATTEN         = 3
SA_MAX_GAIN          = 2
SA_MIN_RBW           = 0.1
SA_MAX_RBW           = 6.0e6
SA_MIN_RT_RBW        = 100.0
SA_MAX_RT_RBW        = 10000.0
SA_MIN_IQ_BANDWIDTH  = 100.0
SA_MAX_IQ_DECIMATION = 128
SA_IQ_SAMPLE_RATE    = 486111.111

# Scales
SA_LOG_SCALE      = 0x0
SA_LIN_SCALE      = 0x1
SA_LOG_FULL_SCALE = 0x2
SA_LIN_FULL_SCALE = 0x3

SA_REF_UNUSED       = 0
SA_REF_INTERNAL_OUT = 1
SA_REF_EXTERNAL_IN  = 2

# Levels
SA_AUTO_ATTEN = -1
SA_AUTO_GAIN = -1

# Detectors
SA_MIN_MAX = 0x0
SA_AVERAGE = 0x1

NO_ERROR = b'No error'

# video units (not sure that these values are correct)
SA_LOG_UNITS = 0x0
SA_VOLT_UNITS = 0x1
SA_POWER_UNITS = 0x2
SA_BYPASS = 0x3

def saGetAPIVersion():
    '''
    This code was written with version 3.0.11
    '''
    f = getattr(sa_dll, 'saGetAPIVersion')
    f.restype = ctypes.c_char_p
    return f()


def saGetErrorString(code):
    f = getattr(sa_dll, 'saGetErrorString')
    f.restype = ctypes.c_char_p

    err_str = f(code)
    if err_str != NO_ERROR:
        print('SA Error: %s' % err_str)

    return err_str


def error_check(err_code):
    return saGetErrorString(err_code)


def saGetSerialNumberList():
    '''
    List of the serial numbers of currently connected devices, max 8.
    '''
    dev_count = ctypes.c_int32()
    s_nums = np.zeros(8, dtype=np.int32)

    f = getattr(sa_dll, 'saGetSerialNumberList')

    err = f(s_nums.ctypes,
            ctypes.byref(dev_count))
    error_check(err)

    return s_nums


def saOpenDeviceBySerialNumber(s_num):
    '''
    Opens device by serial number, returns a device ID (or handle) for
    communication afterwards.  May take several seconds.
    '''
    dev_id = ctypes.c_int32(0)

    f = getattr(sa_dll, 'saOpenDeviceBySerialNumber')

    err = f(ctypes.byref(dev_id),
            ctypes.c_int32(s_num))
    err_code = error_check(err)

    return err_code, dev_id.value


def sa_call(dev_id, func_call, *args):
    '''
    Standard format for calls to an already open device.
    '''
    f = getattr(sa_dll, func_call)

    err = f(ctypes.c_int32(dev_id), *args)
    return error_check(err)


def saCloseDevice(dev_id):
    sa_call(dev_id, 'saCloseDevice')


def saInitiate(dev_id, mode=SA_SWEEPING):
    '''
    Sets mode of operation for the device.  We will normally use SA_SWEEPING
    which is a sweep on-demand.  Other options are externally triggered
    sweeps and streaming data.

    Must be called after changing configuration settings.
    '''
    return sa_call(dev_id, 'saInitiate',
                   ctypes.c_int32(mode),
                   ctypes.c_uint32(0))


def saConfigAcquisition(dev_id, detector=SA_AVERAGE, scale=SA_LOG_SCALE):
    '''
    Configures aquisition mode.  We'll almost always use SA_AVERAGE
    and SA_LOG_SCALE, but you can also obtain min/max data or data in a linear
    scale.  In SA_LOG_SCALE data is given in nominally calibrated dBm, in
    SA_LIN_SCALE data is in millivolts.  In the _FULL scales the data are
    directly from the ADC, which is not terribly useful.
    '''
    assert detector == SA_AVERAGE, 'Min/max not implemented.'

    print('****saConfigAcquisition****')
    err_code = sa_call(dev_id, 'saConfigAcquisition',
                       ctypes.c_int32(detector),
                       ctypes.c_int32(scale))
    print('****saConfigAcquisition done****')
    return err_code

def saConfigProcUnits(dev_id, units=SA_POWER_UNITS):
    '''
    Configures aquisition mode.  We'll almost always use SA_AVERAGE
    and SA_LOG_SCALE, but you can also obtain min/max data or data in a linear
    scale.  In SA_LOG_SCALE data is given in nominally calibrated dBm, in
    SA_LIN_SCALE data is in millivolts.  In the _FULL scales the data are
    directly from the ADC, which is not terribly useful.
    '''

    print('****saConfigProcUnits****')
    err_code = sa_call(dev_id, 'saConfigProcUnits',
                       ctypes.c_int32(units))
    print('****saConfigProcUnits done****')
    return err_code


def saQueryRealTimeFrameInfo(dev_id):
    '''
    Returns the current sweep start, number of steps, and step size
    '''
    frame_width = ctypes.c_int32(0)
    frame_height = ctypes.c_int32(0)

    err_code = sa_call(dev_id, 'saQueryRealTimeFrameInfo',
                       ctypes.byref(frame_width),
                       ctypes.byref(frame_height))

    frame_width = frame_width.value
    frame_height = frame_height.value

    return err_code, frame_width, frame_height


def saQuerySweepInfo(dev_id):
    '''
    Returns the current sweep start, number of steps, and step size
    '''
    sweep_length = ctypes.c_int32(0)
    start_freq = ctypes.c_double(0)
    bin_size = ctypes.c_double(0)

    err_code = sa_call(dev_id, 'saQuerySweepInfo',
                       ctypes.byref(sweep_length),
                       ctypes.byref(start_freq),
                       ctypes.byref(bin_size))

    sweep_length = sweep_length.value
    start_freq = start_freq.value
    bin_size = bin_size.value

    xaxis = np.arange(sweep_length)*bin_size + start_freq
    return err_code, sweep_length, start_freq, bin_size, xaxis


def saGetRealTimeSweep(dev_id):
    ret = saQuerySweepInfo(dev_id)
    err_code, sweep_length, start_freq, bin_size, xaxis = ret
    sweeplen = len(xaxis)

    err_code, frame_width, frame_height = saQueryRealTimeFrameInfo(dev_id)
    sweep_buff = np.empty(sweeplen, dtype=np.double)
    frame_buff = np.empty((frame_height, frame_width), dtype=np.double)
    err_code = sa_call(dev_id, 'saGetRealTimeFrame',
                       sweep_buff.ctypes,
                       frame_buff.ctypes)
    return err_code, xaxis, sweep_buff, frame_buff


def saGetSweep(dev_id):
    '''
    This assumes we're in average mode.  If you really want min/max the
    buffers have different data and the return needs to be modified.
    '''
    ret = saQuerySweepInfo(dev_id)
    err_code, sweep_length, start_freq, bin_size, xaxis = ret
    sweeplen = len(xaxis)

    min_buff = np.empty(sweeplen, dtype=np.double)
    max_buff = np.empty(sweeplen, dtype=np.double)

    err_code = sa_call(dev_id, 'saGetSweep_64f',
                       min_buff.ctypes,
                       max_buff.ctypes)
    return err_code, xaxis, min_buff


def saQueryTemperature(dev_id):
    '''
    This gives you the internal temperature (C) of the device.  For reasons.
    Device has to be in idle mode (aborted) to get a new value.
    '''
    temp = ctypes.c_float(0)

    err_code = sa_call(dev_id, 'saQueryTemperature',
                       ctypes.byref(temp))

    return err_code, temp.value


def saAbort(dev_id):
    '''
    Puts the device in idle mode.  Needs to be initiated to use again.
    '''
    return sa_call(dev_id, 'saAbort')


def saSetTimebase(dev_id, timebase=SA_REF_EXTERNAL_IN):
    '''
    Calling with SA_REF_EXTERNAL_IN attempts to use the external 10 MHz
    reference.  None is found the error will reflect that, and the internal
    reference will be used.  SA_REF_EXTERNAL_OUT is if you want the SA124 to
    generate a 10 MHz reference, which seems unlikely.
    '''
    return sa_call(dev_id, 'saSetTimebase',
                   ctypes.c_int32(timebase))


def saConfigSweepCoupling(dev_id, rbw, vbw, reject=SA_TRUE):
    '''
    The resolution bandwidth, or RBW, represents the bandwidth of spectral
    energy represented in each frequency bin. For example, with an RBW of 10
    kHz, the amplitude value for each bin would represent the total energy
    from 5 kHz below to 5 kHz above the bins center.

    The video bandwidth, or VBW, is applied after the signal has been converted
    to frequency domain as power, voltage, or log units. It is implemented as
    a simple rectangular window, averaging the amplitude readings for each
    frequency bin over several overlapping FFTs. A signal whose amplitude is
    modulated at a much higher frequency than the VBW will be shown as an
    average, whereas amplitude modulation at a lower frequency will be shown
    as a minimum and maximum value.

    Available RBWs are [0.1Hz – 100kHz] and 250kHz. '''
    assert rbw > SA_MIN_RBW, 'RBW below minimum: %f < %f' % (rbw, SA_MIN_RBW)
    assert rbw < SA_MAX_RBW, 'RBW above maximum: %f > %f' % (rbw, SA_MAX_RBW)

    return sa_call(dev_id, 'saConfigSweepCoupling',
                   ctypes.c_double(rbw),
                   ctypes.c_double(vbw),
                   ctypes.c_bool(reject))


def saConfigCenterSpan(dev_id, center, span):
    '''
    Set the sweep frequencies.  The precise settings will not be what are
    assigned here, but they can be found from saQuerySweepInfo.

    '''
    f_min = np.round(center-span/2, -3)
    f_max = np.round(center+span/2, -3)

    assert f_min > SA124_MIN_FREQ, 'f_min below \
           minimum: %f < %f' % (f_min, SA124_MIN_FREQ)
    assert f_max < SA124_MAX_FREQ, 'f_max above \
           maximum: %f > %f' % (f_max, SA124_MAX_FREQ)
    assert span > 1.0, 'Minimum span is 1 Hz'

    return sa_call(dev_id, 'saConfigCenterSpan',
                   ctypes.c_double(np.round(center, -3)),
                   ctypes.c_double(np.round(span, -3)))


def saConfigLevel(dev_id, level):
    '''
    Sets reference level in dBm.
    '''
    assert level < SA_MAX_REF, 'level above \
           maximum: %f > %f' % (level, SA_MAX_REF)

    return sa_call(dev_id, 'saConfigLevel',
                   ctypes.c_double(level))


def saReadSingleFreq(dev_id, freq, n_av=1, verify_freq=True,
                     set_zeroif_params=True):
    '''
    This function is for mixer tuning.  It's effectively zero-IF mode.
    The SA124B has a zero IF mode you can access from the Spike software,
    but it's not documented in the API.  (It is documented for the BB
    series analyzers.)

    This function becomes notably faster without the verification step,
    as well as without setting the zeroif_params.  If you're going to be
    looking at a frequency more than once (as you do when tuning a mixer),
    there's no need to reset the zeroif_params or re-verify the frequency.
    I recommend only doing those on the first call.

    There's not too much of a need for averaging because the device is
    quite sensitive.
    '''
    if set_zeroif_params:
        saConfigSweepCoupling(dev_id, 250e3, 250e3)
    err_code = saConfigCenterSpan(dev_id, freq, 250e3)
    saInitiate(dev_id, SA_SWEEPING)
    time.sleep(0.25)

    if verify_freq:
        ret = saQuerySweepInfo(dev_id)
        err_code, sweep_length, start_freq, bin_size, xaxis = ret
        actual_freq = start_freq + round(sweep_length/2)*bin_size
        diff = np.abs(freq-actual_freq)
        if diff > 100e3:
            raise Exception('Frequency set inaccurate')

    ys = []
    err_code, xs, y = saGetSweep(dev_id)

    idx = len(y)//2
    ys.append(y[idx])
    if n_av > 1:
        for i in range(n_av-1):
            err_code, x, y = saGetSweep(dev_id)
            ys.append(y[idx])
    else:
        pass
    ys = 10**np.array(np.array(ys)/10.0)
    y = np.mean(ys)
    return 10 * np.log10(y)


class SA124B(DllInstrument):
    ''' Driver for SA124B Signal Hound spectrum analyzer

    '''
    
    library = 'sa_api.dll'
    
    def __init__(self, connection_infos, mode=SA_SWEEPING,
                 caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super(SA124B, self).__init__(connection_infos, caching_allowed,
                                     caching_permissions, auto_open)
        self.mode = mode

        if auto_open:
            serial = saGetSerialNumberList()[0]
            assert serial != 0
            self.open_connection(serial)

    def open_connection(self, serial):
        print('OPEN CONNECTION')
        self.error_list = []
        self.vbw, self.rbw = 250e3, 250e3

        s_nums = saGetSerialNumberList()
        if not (serial in s_nums):
            msg = 'Unable to find SA124B with serial %s: \
                   available serial numbers include %i' % (serial, s_nums[0])
            raise Exception(msg)
        self._serialno = serial

        err, self._devid = saOpenDeviceBySerialNumber(serial)
        if err != NO_ERROR:
            raise Exception(err)

        saConfigLevel(self._devid, -10)
        self.do_get_ext_ref()
        self._init_freq()

    def close_connection(self):
        self._close()

    def _close(self):
        saCloseDevice(self._devid)

    def _init_freq(self):
        self.do_set_rbw_vbw(1e3, 1e3)
        self.do_set_f0_span(6e9, 250e3)

    def _initiate(self):
        saInitiate(self._devid, mode=self.mode)

    def do_get_error(self):
        '''
        Error list is update every call.  There is no device query.
        '''
        while len(self.error_list) > 1 and self.error_list[-1] == NO_ERROR:
            self.error_list.pop()

        if len(self.error_list) > 1:
            return self.error_list.pop()
        else:
            return 'Error list empty'

    def do_get_dev_id(self):
        return self._devid

    def do_get_serial(self):
        return self._serialno

    def do_get_vbw(self):
        # The API doesn't have a device query.
        return self.vbw

    def do_get_rbw(self):
        # The API doesn't have a device query.
        return self.rbw

    def do_get_temperature(self):
        saAbort(self._devid)
        err_code, temp = saQueryTemperature(self._devid)
        self.error_list.append(err_code)
        self._initiate()
        return temp

    def do_get_center_frequency(self):
        ret = saQuerySweepInfo(self._devid)
        err_code, sweep_length, start_freq, bin_size, xaxis = ret
        self.error_list.append(err_code)
        return start_freq + round(sweep_length/2)*bin_size

    def do_get_span(self):
        ret = saQuerySweepInfo(self._devid)
        err_code, sweep_length, start_freq, bin_size, xaxis = ret
        self.error_list.append(err_code)
        return sweep_length*bin_size

    def do_set_level(self, level):
        saConfigLevel(self._devid, level)

    def do_set_center_frequency(self, freq):
        span = self.do_get_span()
        err_code = saConfigCenterSpan(self._devid, freq, span)
        self._initiate()
        self.error_list.append(err_code)
        return freq

    def do_set_span(self, span):
        center_frequency = self.do_get_center_frequency()

        err_code = saConfigCenterSpan(self._devid, center_frequency, span)
        self._initiate()
        self.error_list.append(err_code)
        return span

    def do_set_f0_span(self, f0, span):
        err_code = saConfigCenterSpan(self._devid, f0, span)
        self._initiate()
        self.error_list.append(err_code)
        return f0, span

    def do_get_ext_ref(self):
        err_code = saSetTimebase(self._devid)
        self._initiate()
        return err_code

    def do_set_rbw_vbw(self, rbw, vbw):
        err_code = saConfigSweepCoupling(self._devid, rbw, vbw)
        self._initiate()
        if err_code == NO_ERROR:
            self.vbw = vbw
            self.rbw = rbw
        self.error_list.append(err_code)
        return vbw

    def do_set_vbw(self, vbw):
        err_code = saConfigSweepCoupling(self._devid, self.rbw, vbw)
        self._initiate()
        if err_code == NO_ERROR:
            self.vbw = vbw
        self.error_list.append(err_code)
        return vbw

    def do_set_rbw(self, rbw):
        err_code = saConfigSweepCoupling(self._devid, rbw, self.vbw)
        self._initiate()
        if err_code == NO_ERROR:
            self.rbw = rbw
        self.error_list.append(err_code)
        return rbw

    def max_sweep(self):
        err_code, xs, ys = saGetSweep(self._devid)
        self.error_list.append(err_code)
        # import matplotlib.pyplot as plt
        # fig, ax = plt.subplots()
        # ax.plot(xs, ys)
        return max(ys)

    def read_single_freq(self, f0, n_av=1):
        self.do_set_center_frequency(f0)
        fset = self.do_get_center_frequency()
        if (fset-f0)/f0 > 1e-6:
            msg = 'Instrument did not set the frequency correctly'
            raise InstrIOError(msg)
        ys = []
        while n_av > 0:
            ys.append(self.max_sweep())
            n_av -= 1
        ys = np.array(ys)
        return 10*np.log10(np.mean(10**(ys/10)))

    def sweep(self):
        saConfigAcquisition(self._devid,
                            detector=SA_AVERAGE, scale=SA_LOG_SCALE)
        saConfigProcUnits(self._devid, units=SA_POWER_UNITS)
        err_code, xs, ys = saGetSweep(self._devid)
        self.error_list.append(err_code)
        return xs, ys

    def real_time_sweep(self, f0=None, mean=False):
        if f0 is not None:
            self.do_set_center_frequency(f0)
        err_code, xs, ys, zs = saGetRealTimeSweep(self._devid)
        self.error_list.append(err_code)
        ys = np.array(ys)
        length = len(ys)
        mean_value = -np.mean(np.log(np.abs(ys[:length//2])))
        if not mean:
            return xs, ys, zs
        else:
            return mean_value


def test_my_sa():
    serial = saGetSerialNumberList()[0]
    assert serial != 0
    connection_infos = {u'serial': serial}
    my_sa = SA124B(connection_infos, mode=SA_SWEEPING)
    xs, y = my_sa.sweep()
    my_sa._close()

    # import matplotlib.pyplot as plt
    # fig, ax = plt.subplots()
    # ax.plot(xs, y)
    # ax.set_title('SWEEP')
    # ax.set_xlabel('Freq')
    # ax.set_ylabel('Signal')


def test_my_sa_real_time():
    serial = saGetSerialNumberList()[0]
    assert serial != 0
    connection_infos = {u'serial': serial}
    my_sa = SA124B(connection_infos, mode=SA_REAL_TIME)
    xs, y, z = my_sa.real_time_sweep()
    my_sa._close()

    # import matplotlib.pyplot as plt
    # fig, ax = plt.subplots()
    # ax.plot(xs, y)
    # ax.set_title('REAL TIME')
    # ax.set_xlabel('Freq')
    # ax.set_ylabel('Signal')


if __name__ == '__main__':
    test_my_sa()
