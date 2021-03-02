# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Drivers for Anapico SignalGenerator using VISA library.

"""
import re
from textwrap import fill
from inspect import cleandoc

from visa import VisaTypeError

from ..driver_tools import (InstrIOError, instrument_property,
                            secure_communication)
from ..visa_tools import VisaInstrument


class Anapico(VisaInstrument):
    """
    Generic driver for Anapico Signal Generators,
    using the VISA library.

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
    """
    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(Anapico, self).__init__(connection_info,
                                      caching_allowed,
                                      caching_permissions,
                                      auto_open)
        self.frequency_unit = 'GHz'
        self.write_termination = '\n'
        self.read_termination = '\n'
        self.timeout = 50000
# The next line sets the timeout before reconnection to 0. This is available
# since firmware version 0.4.106 and avoids the Anapico generator to freeze
# upon unproperly closed connections (for instance if exopy crashes)
# no need to turn the generator OFF and ON with this line
# here if the explanation from the support team at Anapico:
# I added a reconnect timeout option. It allows to reconnect to an
# inactive link that has never been closed. The timeout defines how long
# the user must wait until the link is considered inactive and reconnect is
# enabled. The default timeout is infinite, meaning no reconnect possible at
# all so it behaves like earlier firmare. In this application the timeout can
# be set to zero so reconnect is always possible immediately.
#
# The command is "SYST:COMM:VXI:RTMO <x>", where "<x>" is the reconnect timeout
# in seconds or "INF" for infinite. If they need to reuse to an unclosed link,
# they should always send "SYST:COMM:VXI:RTMO 0" immediately after opening a
# connection.
        self.write("SYST:COMM:VXI:RTMO 0")

    @instrument_property
    @secure_communication()
    def frequency(self):
        """Frequency of the output signal.

        """
        freq = self.ask_for_values('FREQ?')
        if freq:
            return freq[0]
        else:
            raise InstrIOError

    @frequency.setter
    @secure_communication()
    def frequency(self, value):
        """Frequency setter method.

        """
        unit = self.frequency_unit
        self.write('FREQ {}{}'.format(value, unit))
        result = self.ask_for_values('FREQ?')
        if result:
            if unit == 'GHz':
                result[0] /= 1e9
            elif unit == 'MHz':
                result[0] /= 1e6
            elif unit == 'KHz':
                result[0] /= 1e3
            if abs(result[0] - value) > 1e-12:
                mes = 'Instrument did not set correctly the frequency.'
                raise InstrIOError(mes)

    @instrument_property
    @secure_communication()
    def power(self):
        """Power of the output signal.

        """
        power = self.ask_for_values('POWER?')[0]
        if power is not None:
            return power
        else:
            raise InstrIOError

    @power.setter
    @secure_communication()
    def power(self, value):
        """Power setter method.

        """
        self.write('POWER {}'.format(value))
        result = self.ask_for_values('POWER?')[0]
        if abs(result - value) > 1e-4:
            raise InstrIOError('Instrument did not set correctly the power')

    @instrument_property
    @secure_communication()
    def phase(self):
        """Phase of the output signal.

        """
        phase = self.ask_for_values('PHASE?')[0]
        if phase is not None:
            return phase
        else:
            raise InstrIOError

    @phase.setter
    @secure_communication()
    def phase(self, value):
        """Phase setter method.

        """
        self.write('PHASE {}'.format(value))
        result = self.ask_for_values('PHASE?')[0]
        if abs(result - value) > 1e-4:
            raise InstrIOError('Instrument did not set correctly the phase')

    @instrument_property
    @secure_communication()
    def output(self):
        """Output state of the source.

        """
        output = self.ask_for_values(':OUTP?')
        if output is not None:
            return bool(output[0])
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
            if self.ask(':OUTPUT?') != '1':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        elif off.match(value) or value == 0:
            self.write(':OUTPUT OFF')
            if self.ask(':OUTPUT?') != '0':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the output'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                        switch_on_off method''').format(value), 80)
            raise VisaTypeError(mess)
            
    @instrument_property
    @secure_communication()
    def mode(self):
        """Frequency mode of the signal generator.

        """
        mode = self.ask('FREQ:MODE?')
        if mode:
            return mode
        else:
            raise InstrIOError
            
    @mode.setter
    @secure_communication()
    def mode(self, value):
        """Frequency mode setter method.
        Can be FIX, LIST, SWE or CHIR.

        """
        if not value in ['FIX', 'LIST', 'SWE', 'CHIR']:
            raise InstrIOError(cleandoc('''Frequency mode should be FIX, LIST, SWE or CHIR.
                                        {} given instead'''.format(value)))
        self.write('FREQ:MODE {}'.format(value))
        res = self.ask('FREQ:MODE?')
        if res != value:
            raise InstrIOError(cleandoc('''frequency mode not set properly'''))
            
    @instrument_property
    @secure_communication()
    def start(self):
        """Start frequency for a chirp or step sweep.

        """
        start = self.ask_for_values('FREQ:STAR?')
        if start:
            return start[0]
        else:
            raise InstrIOError
            
    @start.setter
    @secure_communication()
    def start(self, value):
        """Start frequency setter method.
            Unit is Hz.
        """
        self.write('FREQ:STAR {}'.format(value))
        res = self.ask_for_values('FREQ:STAR?')
        if res[0] != value:
            raise InstrIOError(cleandoc('''start frequency not set properly'''))
            
    @instrument_property
    @secure_communication()
    def stop(self):
        """Stop frequency for a chirp or step sweep.

        """
        stop = self.ask_for_values('FREQ:STOP?')
        if stop:
            return stop[0]
        else:
            raise InstrIOError
            
    @stop.setter
    @secure_communication()
    def stop(self, value):
        """Stop frequency setter method.
            Unit is Hz.
        """
        self.write('FREQ:STOP {}'.format(value))
        res = self.ask_for_values('FREQ:STOP?')
        if res[0] != value:
            raise InstrIOError(cleandoc('''stop frequency not set properly'''))
        
    @secure_communication()
    def abort(self):
        """Abort sweep in progress.

        """
        self.write('ABOR')    
        
    @instrument_property
    @secure_communication()
    def init(self):
        """Arms trigger.

        """
        return
            
    @init.setter
    @secure_communication()
    def init(self, value):
        """Arms trigger
            Can be IMM, ON or OFF

        """
        if not value in ['IMM', 'ON', 'OFF']:
            raise InstrIOError(cleandoc('''Frequency mode should be IMM, ON or OFF.
                                        {} given instead'''.format(value)))
        if value != 'IMM':
            value = 'CONT ' + value
        self.write(':INIT:{}'.format(value))
            
    @instrument_property
    @secure_communication()
    def pm_state(self):
        """Pulse modulation getter method

        """
        pm_state = self.ask_for_values('SOURce:PULM:STATE?')
        if pm_state is not None:
            return bool(pm_state[0])
        else:
            mes = 'Signal generator did not return its pulse modulation state'
            raise InstrIOError(mes)

    @pm_state.setter
    @secure_communication()
    def pm_state(self, value):
        """Pulse modulation setter method.

        """
        # TODO: write checks
        self.write('SOURce:PULM:SOURce EXT')
        self.write('SOURce:PULM:POLarity NORMal')
        self.write('SOURce:PULM:TRIGger:EXTernal:IMPedance G50')
        on = re.compile('on', re.IGNORECASE)
        off = re.compile('off', re.IGNORECASE)
        if on.match(value) or value == 1:
            self.write('SOURce:PULM:STATE ON')
            if self.ask('SOURce:PULM:STATE?') != '1':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the pulse modulation state'''))
        elif off.match(value) or value == 0:
            self.write('SOURce:PULM:STATE OFF')
            if self.ask('SOURce:PULM:STATE?') != '0':
                raise InstrIOError(cleandoc('''Instrument did not set correctly
                                        the pulse modulation state'''))
        else:
            mess = fill(cleandoc('''The invalid value {} was sent to
                        switch_on_off method''').format(value), 80)
            raise VisaTypeError(mess)
            
    @instrument_property
    @secure_communication()
    def reference(self):
        """Reference source.

        """
        ref = self.ask('ROSC:SOUR?')
        if ref:
            return ref
        else:
            raise InstrIOError

    @reference.setter
    @secure_communication()
    def reference(self, value):
        """Reference source setter method.
           Can be INTernal or EXTernal.

        """
        if value in ['INT', 'EXT']:
            self.write('ROSC:SOUR {}'.format(value))
            result = self.ask('ROSC:SOUR?')
            if result != value:
                raise InstrIOError(cleandoc('''reference not set properly'''))
        else:
            raise InstrIOError(cleandoc('''reference should be INT or EXT.
                                        {} given instead'''.format(value)))
                                        
    @instrument_property
    @secure_communication()
    def sweep_number(self):
        """Number of times a given sweep is executed.

        """
        nb = self.ask_for_values('SWE:COUN?')
        if nb:
            return nb
        else:
            raise InstrIOError
            
    @sweep_number.setter
    @secure_communication()
    def sweep_number(self, value):
        """Number of sweeps setter method.
           A negative value stands for an infinite number of sweeps.

        """
        if value < 0:
            value = 'INF'
            self.write('SWE:COUN {}'.format(value))
            res = self.ask('SWE:COUN?')
        else:
            self.write('SWE:COUN {}'.format(value))
            res = self.ask_for_values('SWE:COUN?')
            res = res[0]
        if res != value:
            raise InstrIOError(cleandoc('''sweep number not set properly'''))
        
    @instrument_property
    @secure_communication()
    def sweep_dwell_time(self):
        """Dwell time.

        """
        t = self.ask_for_values('SWE:DWEL?')
        if t:
            return t[0]
        else:
            raise InstrIOError
            
    @sweep_dwell_time.setter
    @secure_communication()
    def sweep_dwell_time(self, value):
        """Dwell time setter method.
            Unit is seconds.

        """
        self.write('SWE:DWEL {}'.format(value))
        
        res = self.ask_for_values('SWE:DWEL?')
        if res[0] != value:
            raise InstrIOError(cleandoc('''sweep dwell time not set properly'''))
            
    @instrument_property
    @secure_communication()
    def sweep_spacing(self):
        """Sweep spacing.

        """
        spacing = self.ask('SWE:SPAC?')
        if spacing:
            return spacing
        else:
            raise InstrIOError
            
    @sweep_spacing.setter
    @secure_communication()
    def sweep_spacing(self, value):
        """Sweep spacing setter method.
        Can be LIN or LOG.

        """
        if not value in ['LIN', 'LOG']:
            raise InstrIOError(cleandoc('''Sweep spacing should be LIN or LOG.
                                        {} given instead'''.format(value)))
        self.write('SWE:SPAC {}'.format(value))
        res = self.ask('SWE:SPAC?')
        if res != value:
            raise InstrIOError(cleandoc('''sweep spacing not set properly'''))
        
    @instrument_property
    @secure_communication()
    def sweep_points(self):
        """Sweep number of points.

        """
        pt = self.ask_for_values('SWE:POIN?')
        if pt:
            return pt[0]
        else:
            raise InstrIOError
            
    @sweep_points.setter
    @secure_communication()
    def sweep_points(self, value):
        """Sweep number of points setter method.

        """
        self.write('SWE:POIN {}'.format(value))
        res = self.ask_for_values('SWE:POIN?')
        if res[0] != value:
            raise InstrIOError(cleandoc('''sweep number of points not set properly'''))
            
    @instrument_property
    @secure_communication()
    def sweep_auto_delay(self):
        """Automatic sweep delay.

        """
        value = self.ask_for_values('SWE:DEL:AUTO?')
        if value:
            return value[0]
        else:
            raise InstrIOError
            
    @sweep_auto_delay.setter
    @secure_communication()
    def sweep_auto_delay(self, value):
        """Automatic sweep delay setter method.
        Can be ON, OFF, 1 or 0.

        """
        if value == 'ON':
            value = 1
        if value == 'OFF':
            value = 0
        if not value in [0, 1]:
            raise InstrIOError(cleandoc('''Automatic sweep delay should be ON, OFF, 1 or 0.
                                        {} given instead'''.format(value)))
        self.write('SWE:DEL:AUTO {}'.format(value))
        res = self.ask_for_values('SWE:DEL:AUTO?')
        if res[0] != value:
            raise InstrIOError(cleandoc('''automatic sweep delay not set properly'''))
            
    @instrument_property
    @secure_communication()
    def lfoutput_source(self):
        """Source of the low frequency output.

        """
        value = self.ask('LFO:SOUR?')
        if value:
            return value
        else:
            raise InstrIOError
            
    @lfoutput_source.setter
    @secure_communication()
    def lfoutput_source(self, value):
        """Source of the low frequency output setter method.
        Can be LFG, PULM or TRIG.

        """
        if not value in ['LFG', 'PULM', 'TRIG']:
            raise InstrIOError(cleandoc('''LFoutput source should be LFG, PULM or TRIG.
                                        {} given instead'''.format(value)))
        self.write('LFO:SOUR {}'.format(value))
        res = self.ask('LFO:SOUR?')
        if res == 'LFGenerator':
            res = 'LFG'
        if res == 'TRIGger':
            res = 'TRIG'
        if res != value:
            raise InstrIOError(cleandoc('''LFoutput source not set properly'''))
            
    @instrument_property
    @secure_communication()
    def lfoutput_state(self):
        """State of the low frequency output.

        """
        value = self.ask_for_values('LFO:STAT?')
        if value:
            return value[0]
        else:
            raise InstrIOError
            
    @lfoutput_state.setter
    @secure_communication()
    def lfoutput_state(self, value):
        """State of the low frequency output setter method.
        Can be ON, OFF, 1 or 0.

        """
        if value == 'ON':
            value = 1
        if value == 'OFF':
            value = 0
        if not value in [0, 1]:
            raise InstrIOError(cleandoc('''LFoutput state should be ON, OFF, 1 or 0.
                                        {} given instead'''.format(value)))
        self.write('LFO:STAT {}'.format(value))
        res = self.ask_for_values('LFO:STAT?')
        if res[0] != value:
            raise InstrIOError(cleandoc('''LFoutput state not set properly'''))
            
    @instrument_property
    @secure_communication()
    def trigger_type(self):
        """Trigger type.

        """
        value = self.ask('TRIG:TYPE?')
        if value:
            return value
        else:
            raise InstrIOError
            
    @trigger_type.setter
    @secure_communication()
    def trigger_type(self, value):
        """Trigger type.
        Can be NORM, GATE or POIN.

        """
        if not value in ['NORM', 'GATE', 'POIN']:
            raise InstrIOError(cleandoc('''Trigger type should be NORM, GATE or POIN.
                                        {} given instead'''.format(value)))
        self.write('TRIG:TYPE {}'.format(value))
        res = self.ask('TRIG:TYPE?')
        if res != value:
            raise InstrIOError(cleandoc('''Trigger type not set properly'''))

    @instrument_property
    @secure_communication()
    def trigger_source(self):
        """Trigger source.

        """
        value = self.ask('TRIG:SOUR?')
        if value:
            return value
        else:
            raise InstrIOError
            
    @trigger_source.setter
    @secure_communication()
    def trigger_source(self, value):
        """Trigger source.
        Can be IMM, EXT, KEY or BUS.

        """
        if not value in ['IMM', 'EXT', 'KEY', 'BUS']:
            raise InstrIOError(cleandoc('''Trigger source should be IMM, EXT, KEY or BUS.
                                        {} given instead'''.format(value)))
        self.write('TRIG:SOUR {}'.format(value))
        res = self.ask('TRIG:SOUR?')
        if res != value:
            raise InstrIOError(cleandoc('''Trigger source not set properly'''))
            
    @instrument_property
    @secure_communication()
    def trigger_slope(self):
        """Trigger slope.

        """
        value = self.ask('TRIG:SLOP?')
        if value:
            return value
        else:
            raise InstrIOError
            
    @trigger_slope.setter
    @secure_communication()
    def trigger_slope(self, value):
        """Trigger slope.
        Can be POS, NEG, NP or PN.

        """
        if not value in ['POS', 'NEG', 'NP', 'PN']:
            raise InstrIOError(cleandoc('''Trigger slope should be POS, NEG, NP or PN.
                                        {} given instead'''.format(value)))
        self.write('TRIG:SLOP {}'.format(value))
        res = self.ask('TRIG:SLOP?')
        if res != value:
            raise InstrIOError(cleandoc('''Trigger slope not set properly'''))
            
    @instrument_property
    @secure_communication()
    def trigger_output_mode(self):
        """Trigger output mode.

        """
        value = self.ask('TRIG:OUTP:MODE?')
        if value:
            return value
        else:
            raise InstrIOError
            
    @trigger_output_mode.setter
    @secure_communication()
    def trigger_output_mode(self, value):
        """Trigger output mode.
        Can be NORM, GATE, POIN or VAL.

        """
        if not value in ['NORM', 'GATE', 'POIN', 'VAL']:
            raise InstrIOError(cleandoc('''Trigger output mode should be NORM, GATE, POIN or VAL.
                                        {} given instead'''.format(value)))
        self.write('TRIG:OUTP:MODE {}'.format(value))
        res = self.ask('TRIG:OUTP:MODE?')
        if res != value:
            raise InstrIOError(cleandoc('''Trigger output mode not set properly'''))

class AnapicoMulti(Anapico):
    """
    Generic driver for Anapico Signal Generators,
    using the VISA library.

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
    """
    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(AnapicoMulti, self).__init__(connection_info,
                                      caching_allowed,
                                      caching_permissions,
                                      auto_open)

    @instrument_property
    @secure_communication()
    def channel(self):
        """Power of the output signal.

        """
        channel = self.ask_for_values('SELect?')[0]
        if channel is not None:
            return channel
        else:
            raise InstrIOError

    @channel.setter
    @secure_communication()
    def channel(self, value):
        """Power setter method.

        """
        self.write(':SELect {}'.format(value))
        result = self.ask_for_values('SELect?')[0]
        if result != value:
            raise InstrIOError('Instrument did not set correctly the channel')