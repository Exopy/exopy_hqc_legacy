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

from visa import VisaTypeError

from ..driver_tools import (InstrIOError, instrument_property,
                            secure_communication)
from ..visa_tools import VisaInstrument

class RohdeSchwarzSMB100A(VisaInstrument):
    """
    Generic driver for Rohde and Schwarz SMB100A SignalGenerator,
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
    This driver has been written for the SMB100A but might work for other
    models using the same SCPI commands.

    """
    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(RohdeSchwarzSMB100A, self).__init__(connection_info,
                                                  caching_allowed,
                                                  caching_permissions,
                                                  auto_open)
        self.frequency_unit = 'GHz'
        self.write_termination = '\n'
        self.read_termination = '\n'
        self.pulsedict={
            "PulseGen": "INT",
            "Ext": "EXT",
            "Random": "RAND"}

    @instrument_property
    @secure_communication()
    def frequency(self):
        """Frequency of the output signal.

        """
        freq = self.query('FREQ?')
        if freq:
            return float(freq)
        else:
            raise InstrIOError

    @frequency.setter
    @secure_communication()
    def frequency(self, value):
        """Frequency setter method.

        """
        unit = self.frequency_unit
        self.write('FREQ {}{}'.format(value, unit))
        result = self.query('FREQ?')
        if result:
            result = float(result)
            if unit == 'GHz':
                result /= 1e9
            elif unit == 'MHz':
                result /= 1e6
            elif unit == 'KHz':
                result /= 1e3
            if abs(result - value) > 1e-12:
                mes = 'Instrument did not set correctly the frequency.'
                raise InstrIOError(mes)

    @instrument_property
    @secure_communication()
    def power(self):
        """Power of the output signal.

        """
        power = self.query('POWER?')
        if power:
            return float(power)
        else:
            raise InstrIOError('Instrument did not return the power')

    @power.setter
    @secure_communication()
    def power(self, value):
        """Power setter method.

        """
        self.write('POWER {}'.format(value))
        result = self.query('POWER?')
        if result:
            if abs(float(result) - value) > 1e-12:
                raise InstrIOError('Instrument did not set correctly the power')
        else:
            raise InstrIOError('Instrument did not return the power')

    @instrument_property
    @secure_communication()
    def output(self):
        """Output state of the source.

        """
        output = self.query(':OUTP?')
        if output:
            return bool(int(output))
        else:
            mes = 'PSG signal generator did not return its output'
            raise InstrIOError(mes)

    @output.setter
    @secure_communication()
    def output(self, value):
        """Output setter method.

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
    def pm_source(self):
        """Pulse modulation getter method

        """
        source = self.query('SOURce:PULM:SOURce?')
        if source:
            return source # EXT, INT or RAND
        else:
            mes = 'Signal generator did not return the pulse modulation source'
            raise InstrIOError(mes)

    @pm_source.setter
    @secure_communication()
    def pm_source(self, value):
        """Pulse modulation setter method.

        """
        # TODO: write checks
        self.write('SOURce:PULM:POLarity NORMal')
        self.write('SOURce:PULM:TRIGger:EXTernal:IMPedance G50')
        source=self.pulsedict[value]
        if source in ['EXT','INT','RAND']:
            self.write('SOURce:PULM:SOURce ' + source)
        if source == 'INT':
            self.write('SOURce:PULM:MODE SINGle')
        newvalue = self.query('SOURce:PULM:SOURce?')
        if '.' in newvalue:
            newvalue = newvalue[:-1]
        if source != newvalue:
            raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the pulse modulation source'''))

    @instrument_property
    @secure_communication()
    def video_state(self):
        """Pulse modulation getter method

        """
        state = self.query('SOURce:PGEN:STATE?')
        if state:
            return bool(int(state))
        else:
            mes = 'Signal generator did not return its pulse modulation state'
            raise InstrIOError(mes)

    @video_state.setter
    @secure_communication()
    def video_state(self, value):
        """Pulse modulation setter method.

        """
        # TODO: write checks
        on = re.compile('on', re.IGNORECASE)
        off = re.compile('off', re.IGNORECASE)
        if on.match(value) or value == 1:
            self.write('SOURce:PGEN:STATE ON')
            if self.query('SOURce:PGEN:STATE?') != '1':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the pulse modulation state'''))
        elif off.match(value) or value == 0:
            self.write('SOURce:PGEN:STATE OFF')
            if self.query('SOURce:PGEN:STATE?') != '0':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the pulse modulation state'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                        switch_on_off method''').format(value), 80)
            raise VisaTypeError(mess)

    @instrument_property
    @secure_communication()
    def pm_state(self):
        """Pulse modulation getter method

        """
        state = self.query('SOURce:PULM:STATE?')
        if state:
            return bool(int(state))
        else:
            mes = 'Signal generator did not return its pulse modulation state'
            raise InstrIOError(mes)

    @pm_state.setter
    @secure_communication()
    def pm_state(self, value):
        """Pulse modulation setter method.

        """
        # TODO: write checks
        on = re.compile('on', re.IGNORECASE)
        off = re.compile('off', re.IGNORECASE)
        if on.match(value) or value == 1:
            self.write('SOURce:PULM:STATE ON')
            if self.query('SOURce:PULM:STATE?') != '1':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the pulse modulation state'''))
        elif off.match(value) or value == 0:
            self.write('SOURce:PULM:STATE OFF')
            if self.query('SOURce:PULM:STATE?') != '0':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the pulse modulation state'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                        switch_on_off method''').format(value), 80)
            raise VisaTypeError(mess)

    @instrument_property
    @secure_communication()
    def pulse_width(self):
        """Pulse width of the output signal.

        """
        width = self.query('SOURce:PULM:WIDTh?')
        if width:
            return float(width)
        else:
            raise InstrIOError('Instrument did not return the pulse width')

    @pulse_width.setter
    @secure_communication()
    def pulse_width(self, value):
        """Pulse width setter method.

        """
        self.write('SOURce:PULM:WIDTh {}'.format(value))
        result = self.query('SOURce:PULM:WIDTh?')
        if result:
            if abs(float(result) - value) > 1e-9:
                raise InstrIOError('Instrument did not set correctly the pulse width')
        else:
            raise InstrIOError('Instrument did not return the pulse width')

    @instrument_property
    @secure_communication()
    def pulse_period(self):
        """Pulse period of the output signal.

        """
        period = self.query('SOURce:PULM:PERiod?')
        if period:
            return float(period)
        else:
            raise InstrIOError('Instrument did not return the pulse period')

    @pulse_period.setter
    @secure_communication()
    def pulse_period(self, value):
        """Pulse period setter method.

        """
        self.write('SOURce:PULM:PERiod {}'.format(value))
        result = self.query('SOURce:PULM:PERiod?')
        if result:
            if abs(float(result) - value) > 1e-9:
                raise InstrIOError('Instrument did not set correctly the pulse period')
        else:
            raise InstrIOError('Instrument did not return the pulse period')

class RohdeSchwarzSMF100A(RohdeSchwarzSMB100A):
    """
    Generic driver for Rohde and Schwarz SMF100A SignalGenerator,
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
    This class will handle any minor difference between SMF100A and SMB100A

    """
    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(RohdeSchwarzSMF100A, self).__init__(connection_info,
                                                  caching_allowed,
                                                  caching_permissions,
                                                  auto_open)
        self.frequency_unit = 'GHz'
        self.write_termination = '\n'
        self.read_termination = '\n'

    @instrument_property
    @secure_communication()
    def video_state(self):
        """Pulse modulation getter method

        """
        state = self.query('SOURce:PGEN:OUTput:STATE?')
        if state:
            return bool(int(state))
        else:
            mes = 'Signal generator did not return its pulse modulation state'
            raise InstrIOError(mes)

    @video_state.setter
    @secure_communication()
    def video_state(self, value):
        """Pulse modulation setter method.

        """
        # TODO: write checks
        on = re.compile('on', re.IGNORECASE)
        off = re.compile('off', re.IGNORECASE)
        if on.match(value) or value == 1:
            self.write('SOURce:PGEN:OUTput:STATE ON')
            if self.query('SOURce:PGEN:OUTput:STATE?') != '1':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the pulse modulation state'''))
        elif off.match(value) or value == 0:
            self.write('SOURce:PGEN:OUTput:STATE OFF')
            if self.query('SOURce:PGEN:OUTput:STATE?') != '0':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the pulse modulation state'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                        switch_on_off method''').format(value), 80)
            raise VisaTypeError(mess)
