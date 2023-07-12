# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2021 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Drivers for Keysight PSG SignalGenerator using VISA library.

"""
import re
from textwrap import fill
from inspect import cleandoc

from pyvisa import VisaTypeError

from ..driver_tools import (InstrIOError, instrument_property,
                            secure_communication)
from ..visa_tools import VisaInstrument


class AgilentPSG(VisaInstrument):
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

        super(AgilentPSG, self).__init__(connection_info, caching_allowed,
                                         caching_permissions, auto_open)
        self.frequency_unit = 'GHz'
        self.phase_unit = 'Deg'
        self.write_termination = '\n'
        self.read_termination = '\n'

    @instrument_property
    @secure_communication()
    def frequency(self):
        """Frequency getter method
        """
        freq = self.query(':FREQuency:FIXed?')
        if freq:
            return float(freq)
        else:
            raise InstrIOError

    @frequency.setter
    @secure_communication()
    def frequency(self, value):
        """Frequency setter method
        """
        unit = self.frequency_unit
        self.write(':FREQuency:FIXed {}{}'.format(value, unit))
        result = self.query(':FREQuency:FIXed?')
        if result:
            result = float(result)
            if unit == 'GHz':
                result /= 10**9
            elif unit == 'MHz':
                result /= 10**6
            elif unit == 'KHz':
                result /= 10**3
            if abs(result - value) > 10**-12:
                mes = 'Instrument did not set correctly the frequency'
                raise InstrIOError(mes)
        else:
            raise InstrIOError('PSG signal generator did not return its frequency')

    @instrument_property
    @secure_communication()
    def power(self):
        """Power getter method
        """
        power = self.query(':POWER?')
        if power:
            return float(power)
        else:
            raise InstrIOError

    @power.setter
    @secure_communication()
    def power(self, value):
        """Power setter method
        """
        self.write(':POWER {}DBM'.format(value))
        result = self.query('POWER?')
        if result:
            if abs(float(result) - value) > 10**-12:
                raise InstrIOError('Instrument did not set correctly the power')
        else:
            raise InstrIOError('PSG signal generator did not return its power')

    @instrument_property
    @secure_communication()
    def output(self):
        """Output getter method
        """
        output = self.query(':OUTPUT?')
        if output:
            return bool(int(output))
        else:
            mes = 'PSG signal generator did not return its output'
            raise InstrIOError(mes)

    @output.setter
    @secure_communication()
    def output(self, value):
        """Output setter method
        """
        on = re.compile('on', re.IGNORECASE)
        off = re.compile('off', re.IGNORECASE)
        if on.match(value) or value == 1:
            self.write(':OUTPUT ON')
            if self.query(':OUTPUT?') != '1':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        elif off.match(value) or value == 0:
            self.write(':OUTPUT OFF')
            if self.query(':OUTPUT?') != '0':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                        switch_on_off method''').format(value), 80)
            raise VisaTypeError(mess)

    @instrument_property
    @secure_communication()
    def phase(self):
        """Phase getter method
        """
        phase = self.query(':PHASe?')
        if phase:
            return float(phase)
        else:
            raise InstrIOError

    @phase.setter
    @secure_communication()
    def phase(self, value):
        """Phase setter method
        """
        pi = 3.141592653589793
        unit = self.phase_unit
        self.write(':PHAS {}{}'.format(value, unit))
        result = self.query(':PHASe?')
        if unit == 'Deg':
            value = value - (value//180)*180
        elif unit == 'Rad':
            value = value - (value//pi)*pi
        if result:
            result = float(result)
            result = result - (result//pi)*pi
            if unit == 'Deg':
                result /= pi/180
            if abs(result - value) > 10**-3:
                mes = 'Instrument did not set correctly the phase'
                raise InstrIOError(mes)
        else:
            raise InstrIOError('PSG signal generator did not return its phase')



