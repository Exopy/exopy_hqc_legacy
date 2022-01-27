# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Drivers for Rohde and Schwarz SignalGenerator using VISA library.

"""
import re
from textwrap import fill
from inspect import cleandoc
import numpy as np

from visa import VisaTypeError

from ..driver_tools import (InstrIOError, instrument_property,
                            secure_communication)
from ..visa_tools import VisaInstrument


class RohdeSchwarzFSV7(VisaInstrument):
    """
    Generic driver for Rohde and Schwarz FSV7 Signalanalyzer,
    using the VISA library.

    This driver does not give access to all the functionnality of the
    instrument but you can extend it if needed. See the documentation of
    the driver_tools module for more details about writing instruments
    drivers.

    Parameters
    ----------
    see the `VisaInstrument` parameters

    Attributes
    ----------


    Notes
    -----
    This driver has been written for the SMB100A but might work for other
    models using the same SCPI commands.

    """
    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(RohdeSchwarzFSV7, self).__init__(connection_info,
                                                  caching_allowed,
                                                  caching_permissions,
                                                  auto_open)
        self.write_termination = '\n'
        self.read_termination = '\n'
        self.check_operation_completion()

    @secure_communication()
    def check_operation_completion(self):
        """
        """
        return bool(int(self.query('*OPC?')))

    @secure_communication()
    def abort_measurement(self):
        """
        """
        self.write('ABOR')

    @secure_communication()
    def read_data(self, trace):
        """
        """
        if self.mode == 'SA':
            self.data_format='REAL,+32'
            self.check_operation_completion()
            rawdata = self.query_binary_values('TRAC? TRACE{}'.format(trace))
            if np.any(rawdata):
                freq = np.linspace(self.start_frequency_SA,
                                   self.stop_frequency_SA,
                                   self.sweep_points_SA)
                return np.rec.fromarrays([freq, np.array(rawdata)],
                                         names=['Frequency', 'SAdata'])
            else:
                raise InstrIOError(cleandoc('''R&S FSV did not return the
                    trace {} data'''.format(trace)))

    @secure_communication()
    def single_trace_measurement(self):
        self.write('INST SAN')
        self.write('INIT:CONT OFF')
        self.write('INIT:IMM')

    @instrument_property
    @secure_communication()
    def mode(self):
        """
        """
        SAorOTHER = self.query('INST:SEL?')
        if SAorOTHER:
            if SAorOTHER == 'SAN':
                return 'SA'
            else:
                return 'OTHER'
        else:
            raise InstrIOError(cleandoc('''R&S FSV did not return its
                    mode'''))

    @mode.setter
    @secure_communication()
    def mode(self, value):
        """
        """
        if value == 'SA':
            self.write('INST:SEL SAN')
        else:
            raise ValueError(cleandoc('''Agilent PSA driver does not handle this
                    mode'''))

    @instrument_property
    @secure_communication()
    def start_frequency_SA(self):
        """Start frequency getter method
        """

        if self.mode == 'SA':
            freq = self.query('FREQ:STAR?')
            if freq:
                return float(freq)
            else:
                raise InstrIOError(cleandoc('''R&S FSV did not return the
                    start frequency'''))
        else:
            raise '''R&S FSV is not in the appropriate mode to get correctly the
                    start frequency'''

    @start_frequency_SA.setter
    @secure_communication()
    def start_frequency_SA(self, value):
        """Start frequency setter method
        """
        if self.mode == 'SA':
            self.write('FREQ:STAR {}'.format(value))
            result = self.query('FREQ:STAR?')
            if result:
                if abs(float(result) - value)/value > 10**-12:
                    raise InstrIOError(cleandoc('''R&S FSV did not set correctly
                    the start frequency'''))
            else:
                raise InstrIOError(cleandoc('''R&S FSV did not set correctly the
                    start frequency'''))
        else:
            raise '''R&S FSV is not in the appropriate mode to set correctly the
                    start frequency'''

    @instrument_property
    @secure_communication()
    def stop_frequency_SA(self):
        """Stop frequency getter method
        """
        if self.mode == 'SA':
            freq = self.query('FREQ:STOP?')
            if freq:
                return float(freq)
            else:
                raise InstrIOError(cleandoc('''R&S FSV did not return the
                    stop frequency'''))
        else:
            raise '''R&S FSV is not in the appropriate mode to get correctly the
                    stop frequency'''

    @stop_frequency_SA.setter
    @secure_communication()
    def stop_frequency_SA(self, value):
        """Stop frequency setter method
        """
        if self.mode == 'SA':
            self.write('FREQ:STOP {}'.format(value))
            result = self.query('FREQ:STOP?')
            if result:
                if abs(float(result) - value)/value > 10**-12:
                    raise InstrIOError(cleandoc('''R&S FSV did not set correctly
                    the stop frequency'''))
            else:
                raise InstrIOError(cleandoc('''R&S FSV did not set correctly the
                    stop frequency'''))
        else:
            raise '''R&S FSV is not in the appropriate mode to set correctly the
                    stop frequency'''

    @instrument_property
    @secure_communication()
    def center_frequency(self):
        """Center frequency getter method
        """
        freq = self.query('FREQ:CENT?')
        if freq:
            return float(freq)
        else:
            raise InstrIOError(cleandoc('''R&S FSV did not return the
                    center frequency'''))

    @center_frequency.setter
    @secure_communication()
    def center_frequency(self, value):
        """center frequency setter method
        """
        self.write('FREQ:CENT {}'.format(value))
        result = self.query('FREQ:CENT?')
        if result:
            if abs(float(result) - value)/value > 10**-12:
                raise InstrIOError(cleandoc('''R&S FSV did not set correctly the
                    center frequency'''))
        else:
            raise InstrIOError(cleandoc('''R&S FSV did not set correctly the
                    center frequency'''))

    @instrument_property
    @secure_communication()
    def span_frequency(self):
        """Span frequency getter method
        """
        if self.mode == 'SA':
            freq = self.query('FREQ:SPAN?')
            if freq:
                return float(freq)
            else:
                raise InstrIOError(cleandoc('''R&S FSV did not return the
                    span frequency'''))

        else:
            raise '''R&S FSV is not in the appropriate mode to get correctly the
                    span frequency'''

    @span_frequency.setter
    @secure_communication()
    def span_frequency(self, value):
        """span frequency setter method
        """
        if self.mode == 'SA':
            self.write('FREQ:SPAN {}'.format(value))
            result = self.query('FREQ:SPAN?')
            if result:
                if abs(float(result) - value)/value > 10**-12:
                    raise InstrIOError(cleandoc('''R&S FSV did not set correctly
                    the span frequency'''))
            else:
                raise InstrIOError(cleandoc('''R&S FSV did not set correctly the
                    span frequency'''))
        else:
            raise '''R&S FSV is not in the appropriate mode to set correctly the
                    span frequency'''

    @instrument_property
    @secure_communication()
    def sweep_time(self):
        """Sweep time getter method
        """
        if self.mode == 'SA':
            sweep = self.query('SWEEP:TIME?')
            if sweep:
                return float(sweep)
            else:
                raise InstrIOError(cleandoc('''R&S FSV did not return the
                    sweep time'''))
        else:
            raise '''R&S FSV is not in the appropriate mode to get correctly the
                    sweep time'''

    @sweep_time.setter
    @secure_communication()
    def sweep_time(self, value):
        """sweep time setter method
        """
        if self.mode == 'SA':
            self.write('SWEEP:TIME {}'.format(value))
            result = self.query('SWEEP:TIME?')
            if result:
                if abs(float(result) - value)/value > 10**-12:
                    raise InstrIOError(cleandoc('''R&S FSV did not set correctly
                    the sweep time'''))
            else:
                raise InstrIOError(cleandoc('''R&S FSV did not set correctly the
                    sweep time'''))
        else:
            raise '''R&S FSV is not in the appropriate mode to set correctly the
                    sweep time'''

    @instrument_property
    @secure_communication()
    def RBW(self):
        """
        """
        rbw = self.query('BWIDth?')
        if rbw:
            return float(rbw)
        else:
            raise InstrIOError(cleandoc('''R&S FSV did not return the
                channel Resolution bandwidth'''))

    @RBW.setter
    @secure_communication()
    def RBW(self, value):
        """
        """
        self.write('BWIDth {}'.format(value))
        result = self.query('BWIDth?')
        if result:
            if abs(float(result) - value) > 10**-12:
                raise InstrIOError(cleandoc('''R&S FSV did not set correctly
                the channel Resolution bandwidth'''))
        else:
            raise InstrIOError(cleandoc('''R&S FSV did not set correctly the
                channel Resolution bandwidth'''))

    @instrument_property
    @secure_communication()
    def VBW_SA(self):
        """
        """
        if self.mode == 'SA':
            vbw = self.query('BWIDth:VID?')
            if vbw:
                return float(vbw)
            else:
                raise InstrIOError(cleandoc('''R&S FSV did not return the
                    channel Video bandwidth'''))
        else:
            raise '''R&S FSV is not in the appropriate mode to set correctly the
                    channel Video bandwidth'''

    @VBW_SA.setter
    @secure_communication()
    def VBW_SA(self, value):
        """
        """
        if self.mode == 'SA':
            self.write('BWIDth:VID {}'.format(value))
            result = self.query('BWIDth:VID?')
            if result:
                if abs(float(result) - value) > 10**-12:
                    raise InstrIOError(cleandoc('''R&S FSV did not set correctly
                    the channel Video bandwidth'''))
            else:
                raise InstrIOError(cleandoc('''R&S FSV did not set correctly the
                    channel Video bandwidth'''))
        else:
            raise '''R&S FSV is not in the appropriate mode to set correctly the
                    channel Video bandwidth'''

    @instrument_property
    @secure_communication()
    def sweep_points_SA(self):
        """
        """
        if self.mode == 'SA':
            points = self.query('SWEep:POINts?')
            if points:
                return int(points)
            else:
                raise InstrIOError(cleandoc('''R&S FSV did not return the
                        sweep point number'''))
        else:
            raise '''R&S FSV is not in the appropriate mode to set correctly the
                    channel Video bandwidth'''

    @sweep_points_SA.setter
    @secure_communication()
    def sweep_points_SA(self, value):
        """
        """
        if self.mode == 'SA':
            self.write('SWEep:POINts {}'.format(value))
            result = self.query('SWEep:POINts?')
            if result:
                if int(result) != value:
                    raise InstrIOError(cleandoc('''R&S FSV did not set correctly the
                        sweep point number'''))
            else:
                raise InstrIOError(cleandoc('''R&S FSV did not set correctly the
                        sweep point number'''))
        else:
            raise '''R&S FSV is not in the appropriate mode to set correctly the
                    channel Video bandwidth'''

    @instrument_property
    @secure_communication()
    def average_count_SA(self):
        """
        """
        if self.mode == 'SA':
            count = self.query('AVERage:COUNt?')
            if count:
                return int(count)
            else:
                raise InstrIOError(cleandoc('''R&S FSV did not return the
                         average count'''))
        else:
            raise '''R&S FSV is not in the appropriate mode to set correctly the
                    channel Video bandwidth'''

    @average_count_SA.setter
    @secure_communication()
    def average_count_SA(self, value):
        """
        """
        if self.mode == 'SA':
            self.write('AVERage:COUNt {}'.format(value))
            result = self.query('AVERage:COUNt?')
            if result:
                if int(result) != value:
                    raise InstrIOError(cleandoc('''R&S FSV did not set correctly the
                         average count'''))
            else:
                raise InstrIOError(cleandoc('''R&S FSV did not set correctly the
                         average count'''))
        else:
            raise '''R&S FSV is not in the appropriate mode to set correctly the
                    channel Video bandwidth'''

    @instrument_property
    @secure_communication()
    def average_state_SA(self):
        """
        """
        if self.mode == 'SA':
            state = self.query('AVERage?')
            if state:
                return state
            else:
                raise InstrIOError(cleandoc('''R&S FSV did not return the
                        average state'''))
        else:
            raise '''R&S FSV is not in the appropriate mode to set correctly the
                    channel Video bandwidth'''

    @average_state_SA.setter
    @secure_communication()
    def average_state_SA(self, value):
        """
        """
        if self.mode == 'SA':
            self.write('AVERage:STATE {}'.format(value))
            result = self.query('AVERage?')
            if result:
                if ( (value=='ON' and int(result)!=1) or 
                     (value=='OFF' and int(result)!=0)  ):
                    raise InstrIOError(cleandoc('''R&S FSV did not set correctly the
                        average state'''))
            else:
                raise InstrIOError(cleandoc('''R&S FSV did not return the
                                               average state'''))
        else:
            raise '''R&S FSV is not in the appropriate mode to set correctly the
                    channel Video bandwidth'''

    @instrument_property
    @secure_communication()
    def data_format(self):
        """
        REAL,+32 - Best for transferring large amounts of measurement data.
                   Can cause rounding errors in frequency data.
        ASCii,+0 - The easiest to implement, but very slow.
                 Use when you have small amounts of data to transfer.
        """
        data_format = self.query('FORMAT:DATA?')
        if '32' in data_format:
            return 'REAL,+32'
        elif '0' in data_format:
            return 'ASC,+0'
        else:
            raise InstrIOError(cleandoc('''R&S FSV did not return the
                    data format'''))

    @data_format.setter
    @secure_communication()
    def data_format(self, value):
        """
        """
        if value == 'REAL,+32':
            datatype = 'REAL,32'
        elif value == 'ASC,+0':
            datatype = 'ASCii,0'

        self.write('FORM {}'.format(datatype))
        result = self.query('FORM?')

        if result.lower() != datatype.lower()[:len(result)]:
            raise InstrIOError(cleandoc('''R&S FSV did not set correctly the
                data format'''))