# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by EcpyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Driver for Windfreaktech SynthHD SignalGenerator using VISA library.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import re
from textwrap import fill
from inspect import cleandoc

from visa import VisaTypeError

from ..driver_tools import (InstrIOError, instrument_property,
                            secure_communication)
from ..visa_tools import VisaInstrument

CONVERSION_FACTORS = {'GHz': {'Hz': 1e9, 'kHz': 1e6, 'MHz': 1e3, 'GHz': 1},
                      'MHz': {'Hz': 1e6, 'kHz': 1e3, 'MHz': 1, 'GHz': 1e-3},
                      'kHz': {'Hz': 1e3, 'kHz': 1, 'MHz': 1e-3, 'GHz': 1e-6},
                      'Hz': {'Hz': 1, 'kHz': 1e-3, 'MHz': 1e-6, 'GHz': 1e-9}}

class SynthHD(VisaInstrument):
    """
    Generic driver for Agilent PSG SignalGenerator, using the VISA library.

    This driver does not give access to all the functionnality of the
    instrument but you can extend it if needed. See the documentation of
    the driver_tools module for more details about writing instruments
    drivers.

    Parameters
    ----------
    see the `VisaInstrument` parameters

    Attributes
    ----------
    frequency_unit : str
        Frequency unit used by the driver. The default unit is 'GHz'. Other
        valid units are : 'MHz', 'KHz', 'Hz'
    frequency : float, instrument_property
        Fixed frequency of the output signal.
    power : float, instrument_property
        Fixed power of the output signal.
    output : bool, instrument_property
        State of the output 'ON'(True)/'OFF'(False).

    Notes
    -----
    This driver has been written for the  but might work for other
    models using the same SCPI commands.

    """
    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        print(connection_info)
        super(SynthHD, self).__init__(connection_info, caching_allowed,
                                         caching_permissions, auto_open)
        self.channel = 0
        self.frequency_unit = 'GHz'
        self.write_termination = ''
        self.read_termination = ''
        self.detuneRef = 10.0 # in MHz
        self.powerRef = 13.0 # in dBm
        self.detuneRef_format = '{:.4f}'.format(self.detuneRef) # in correct format for inst

    @instrument_property
    @secure_communication()
    def frequency(self):
        """Frequency getter method
        """
        self.write('C'+str(self.channel))
        self.write('f?')
        freq = self.read()
        if freq:
            return freq
        else:
            raise InstrIOError

    @frequency.setter
    @secure_communication()
    def frequency(self, value):
        """Frequency setter method
        """
        unit = self.frequency_unit
        channel = self.channel

        valueMHz = value*CONVERSION_FACTORS[unit]['MHz']
        valueMHz_format = '{:.4f}'.format(valueMHz)
        print(str(valueMHz_format))
        self.write('C'+str(channel))
        self.write('f'+str(valueMHz_format))
        #self.write('C1')
        #self.write('f'+str(valueMHz_format+self.detuneRef_format))
        self.write('f?') # asks for frequency of current channel
        result = float(self.read()) # returns frequency in MHz
        if abs(result - valueMHz) > 10**-12:
            mes = 'Instrument did not set correctly the frequency'
            raise InstrIOError(mes)

    @instrument_property
    @secure_communication()
    def power(self):
        """Power getter method
        """
        self.write('C'+str(self.channel))
        self.write('W?')
        power = self.read()
        if power is not None:
            return power
        else:
            raise InstrIOError

    @power.setter
    @secure_communication()
    def power(self, value):
        """Power setter method
        """
        self.write('C'+str(self.channel))
        self.write('W'+str('{:.4f}'.format(value)))
#        self.write('C1')
#        self.write('W'+str(self.powerRef))

        self.write('W?')
        result = float(self.read())
        if abs(result - value) > 10**-12:
            raise InstrIOError('Instrument did not set correctly the power')

    @instrument_property
    @secure_communication()
    def output(self):
        """Output getter method
        """
        channel = self.channel
        self.write('C'+str(channel))
        self.write('E?r?')
        outputE = self.read()
        outputr = self.read()
        if outputE is not None and outputr is not None:
            outputE = outputE[0]
            outputr = outputr[0]
            if outputE == '1' and outputr == '1':
                return True
            if outputE == '0' and outputr == '0':
                return False
            else:
                mes = '''The synthHD is in an intermediate state,
                neither fully quiet, nor fully operational '''
                raise InstrIOError(mes)
        else:
            mes = 'SynthHD signal generator did not return its output'
            raise InstrIOError(mes)

    @output.setter
    @secure_communication()
    def output(self, value):
        """Output setter method
        """
        channel = self.channel
        self.write('C'+str(channel))
        on = re.compile('on', re.IGNORECASE)
        off = re.compile('off', re.IGNORECASE)
        if on.match(value) or value == 1:
            self.write('E1r1')
            if not self.output:
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        elif off.match(value) or value == 0:
            self.write('E0r0')
            if self.output:
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                        switch_on_off method''').format(value), 80)
            raise VisaTypeError(mess)
