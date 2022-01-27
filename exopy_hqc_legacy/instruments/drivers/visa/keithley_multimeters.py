# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2022 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Driver for Keithley instruments using VISA library.

"""
from ..driver_tools import (InstrIOError, secure_communication,
                            instrument_property)
from ..visa_tools import VisaInstrument
from inspect import cleandoc
import logging

class Keithley2000(VisaInstrument):
    """Driver for Keithley 2000 using the VISA library

    This driver does not give access to all the functionnality of the
    instrument but you can extend it if needed. See the documentation of the
    driver_tools package for more details about writing instruments drivers.

    Parameters
    ----------
    see the `VisaInstrument` parameters

    Attributes
    ----------
    function : str, instrument_property
        Current function of the multimeter. Can be : 'VOLT:DC', 'VOLT:AC',
        'CURR:DC', 'CURR:AC', 'RES'. This instrument property is cached by
        default.

    Methods
    -------
    read_voltage_dc(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the DC voltage read by the instrument. Can change the function
        if needed.
    read_voltage_ac(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the AC voltage read by the instrument. Can change the function
        if needed.
    read_res(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the resistance read by the instrument. Can change the function
        if needed.
    read_current_dc(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the DC current read by the instrument. Can change the function
        if needed.
    read_current_ac(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the AC current read by the instrument. Can change the function
        if needed.

    """
    caching_permissions = {'function': True}

    protocoles = {'GPIB': 'INSTR'}

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`.

        """
        super(Keithley2000, self).open_connection(**para)
        self.write_termination = '\n'
        self.read_termination = '\n'

    @instrument_property
    @secure_communication()
    def function(self):
        """Function setter

        """
        value = self.query('FUNCtion?')
        if value:
            return value
        else:
            raise InstrIOError('Keithley2000 : Failed to return function')

    @function.setter
    @secure_communication()
    def function(self, value):
        self.write('FUNCtion "{}"'.format(value))
        # The Keithley returns "VOLT:DC" needs to remove the quotes
        if not(self.query('FUNCtion?')[1:-1].lower() == value.lower()):
            raise InstrIOError('Keithley2000: Failed to set function')

    @secure_communication()
    def read_voltage_dc(self, mes_range='DEF', mes_resolution='DEF'):
        """Return the DC voltage read by the instrument.

        Perform a direct reading without any waiting. Can return identical
        values if the instrument is read more often than its integration time.
        The arguments are unused and here only to make this driver and the
        agilent driver compatible.

        """
        if self.function != 'VOLT:DC':
            self.function = 'VOLT:DC'

        value = self.query('FETCh?')
        if value:
            return float(value)
        else:
            raise InstrIOError('Keithley2000: DC voltage measure failed')

    @secure_communication()
    def read_voltage_ac(self, mes_range='DEF', mes_resolution='DEF'):
        """Return the AC voltage read by the instrument.

        Perform a direct reading without any waiting. Can return identical
        values if the instrument is read more often than its integration time.
        The arguments are unused and here only to make this driver and the
        agilent driver compatible.

        """
        if self.function != 'VOLT:AC':
            self.function = 'VOLT:AC'

        value = self.query('FETCh?')
        if value:
            return float(value)
        else:
            raise InstrIOError('Keithley2000: AC voltage measure failed')

    @secure_communication()
    def read_resistance(self, mes_range='DEF', mes_resolution='DEF'):
        """
        Return the resistance read by the instrument.

        Perform a direct reading without any waiting. Can return identical
        values if the instrument is read more often than its integration time.
        The arguments are unused and here only to make this driver and the
        agilent driver compatible.

        """
        if self.function != 'RES':
            self.function = 'RES'

        value = self.query('FETCh?')
        if value:
            return float(value)
        else:
            raise InstrIOError('Keithley2000: Resistance measure failed')

    @secure_communication()
    def read_current_dc(self, mes_range='DEF', mes_resolution='DEF'):
        """Return the DC current read by the instrument.

        Perform a direct reading without any waiting. Can return identical
        values if the instrument is read more often than its integration time.
        The arguments are unused and here only to make this driver and the
        agilent driver compatible.

        """
        if self.function != 'CURR:DC':
            self.function = 'CURR:DC'

        value = self.query('FETCh?')
        if value:
            return float(value)
        else:
            raise InstrIOError('Keithley2000: DC current measure failed')

    @secure_communication()
    def read_current_ac(self, mes_range='DEF', mes_resolution='DEF'):
        """Return the AC current read by the instrument.

        Perform a direct reading without any waiting. Can return identical
        values if the instrument is read more often than its integration time.
        The arguments are unused and here only to make this driver and the
        agilent driver compatible.

        """
        if self.function != 'CURR:AC':
            self.function = 'CURR:AC'

        value = self.query('FETCh?')
        if value:
            return float(value)
        else:
            raise InstrIOError('Keithley2000: AC current measure failed')

    @secure_communication()
    def check_connection(self):
        """Check wether or not a front panel user set the instrument in local.

        If a front panel user set the instrument in local the cache can be
        corrupted and should be cleared.

        """
        val = ('{0:08b}'.format(int(self.query('*ESR'))))[::-1]
        if val:
            return val[6]


class Keithley2450(VisaInstrument):
    """Driver for Keithley 2450 using the VISA library

    This driver does not give access to all the functionnality of the
    instrument but you can extend it if needed. See the documentation of the
    driver_tools package for more details about writing instruments drivers.

    Parameters
    ----------
    see the `VisaInstrument` parameters

    Attributes
    ----------
    function : str, instrument_property
        Present function of the source. Can be : 'SourceI:MeasV', 'SourceI:MeasI',
        'SourceV:MeasI', 'SourceV:MeasV', 'RES'. This instrument property is cached by
        default.

    Methods
    -------
    read_voltage_dc(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the DC voltage read by the instrument. Otherwise raises Error.
    read_voltage_ac(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the AC voltage read by the instrument. Otherwise raises Error.
    read_res(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the resistance read by the instrument. Otherwise raises Error.
    read_current_dc(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the DC current read by the instrument. Otherwise raises Error.
    read_current_ac(mes_range = 'DEF', mes_resolution = 'DEF')
        Return the AC current read by the instrument. Otherwise raises Error.

    """
    caching_permissions = {'function': True}

    protocoles = {'GPIB': 'INSTR'}

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`.

        """
        super(Keithley2450, self).open_connection(**para)
        self.write_termination = '\n'
        self.read_termination = '\n'

    ### Function

    @instrument_property
    @secure_communication()
    def function(self):
        """Function setter

        """
        value = self.query('SOUR:FUNC?')
        if value:
            return value
        else:
            raise InstrIOError('Keithley2450 : Failed to return function')

    @function.setter
    @secure_communication()
    def function(self, value):
        self.write('SOUR:FUNC "{}";'.format(value))
        # The Keithley returns "VOLT:DC" needs to remove the quotes
        if not(self.query('SOUR:FUNC?')[1:-1].lower() == value.lower()):
            raise InstrIOError('Keithley2450: Failed to set function')

    ### Sense function

    @instrument_property
    @secure_communication()
    def sense_function(self):
        """Function setter

        """
        value = self.query('SENS:FUNC?')
        if value:
            return value
        else:
            raise InstrIOError('Keithley2450 : Failed to return sense function')

    @sense_function.setter
    @secure_communication()
    def sense_function(self, value):
        self.write('SENS:FUNC "{}";'.format(value))
        # The Keithley returns "VOLT:DC" needs to remove the quotes
        if not(self.query('SENS:FUNC?')[1:-1].lower() == value.lower()):
            raise InstrIOError('Keithley2450: Failed to set sense function')

    ### Voltage output

    @instrument_property
    @secure_communication()
    def voltage(self):
        """Voltage getter method. NB: does not check the current function.

        """
        voltage = self.query(":SOUR:VOLT?")
        if voltage:
            return float(voltage)
        else:
            raise InstrIOError('Instrument did not return the voltage')

    @voltage.setter
    @secure_communication()
    def voltage(self, set_point):
        """Voltage setter method. NB: does not check the current function.

        """
        self.write(":SOUR:VOLT:LEV {}".format(set_point))
        value = self.query('SOUR:VOLT?')
        # to avoid floating point rouding
        if abs(float(value) - round(set_point, 9)) > 1e-9:
            raise InstrIOError('Instrument did not set correctly the voltage')

    ### Current compliance

    @instrument_property
    @secure_communication()
    def current_compliance(self):
        """Current compliance getter method. NB: does not check the present function.

        """
        lim_curr = self.query(":SOUR:VOLT:ILIM?")
        if lim_curr:
            return float(lim_curr)
        else:
            raise InstrIOError('Instrument did not return the compliance current')

    @secure_communication()
    def read_current_compliance(self):
        """Wrapper for the current compliance getter that checks for the mode

        """
        if self.function == 'VOLT':
            return self.current_compliance
        msg = ('Instrument cannot use current compliance when in current mode')
        raise InstrIOError(msg)

    @current_compliance.setter
    @secure_communication()
    def current_compliance(self, value):
        """Current compliance setter method. NB: does not check the present function.

        """
        self.write(":SOUR:VOLT:ILIM {}".format(value))
        feedback = self.query('SOUR:VOLT:ILIM?')
        # to avoid floating point rouding
        if abs(float(feedback) - round(value, 12)) > 1e-12:
            raise InstrIOError('Instrument did not set correctly the compliance')

    @secure_communication()
    def read_voltage_dc(self, mes_range='DEF', mes_resolution='DEF'):
        """Return the DC voltage read by the instrument.

        Perform a direct reading without any waiting. Can return identical
        values if the instrument is read more often than its integration time.
        The arguments are unused and here only to make this driver and the
        agilent driver compatible.

        """
        if self.function != 'CURR':
            raise InstrIOError('Keithley2450: Current source mode required to read voltage')
        if self.sense_function[1:-1] != 'VOLT:DC':
            raise InstrIOError('Keithley2450: Voltage sense mode required to read voltage, not {}'.format(self.sense_function))

        value = self.query('READ?')
        if value:
            return float(value)
        else:
            raise InstrIOError('Keithley2450: DC voltage measure failed')

    @secure_communication()
    def read_current_dc(self, mes_range='DEF', mes_resolution='DEF'):
        """Return the DC current read by the instrument.

        Perform a direct reading without any waiting. Can return identical
        values if the instrument is read more often than its integration time.
        The arguments are unused and here only to make this driver and the
        agilent driver compatible.

        """
        if self.function != 'VOLT':
            raise InstrIOError('Keithley2450: Voltage source mode required to read voltage')
        if self.sense_function[1:-1] != 'CURR:DC':
            raise InstrIOError('Keithley2450: Current sense mode required to read voltage, not {}'.format(self.sense_function))

        value = self.query('READ?')
        if value:
            return float(value)
        else:
            raise InstrIOError('Keithley2450: DC current measure failed')

    @secure_communication()
    def check_connection(self):
        """Check wether or not a front panel user set the instrument in local.

        If a front panel user set the instrument in local the cache can be
        corrupted and should be cleared.

        """
        val = ('{0:08b}'.format(int(self.query('*ESR'))))[::-1]
        if val:
            return val[6]

class Keithley6221(VisaInstrument):
    """Driver for Keithley 6221 using the VISA library

    This driver does not give access to all the functionnality of the
    instrument but you can extend it if needed. See the documentation of the
    driver_tools package for more details about writing instruments drivers.

    Parameters
    ----------
    see the `VisaInstrument` parameters

    Attributes
    ----------
    output : str, instrument_property
        Present function of the source. Can be : 'SourceI:MeasV', 'SourceI:MeasI',
        'SourceV:MeasI', 'SourceV:MeasV', 'RES'. This instrument property is cached by
        default.

    Methods
    -------


    """
    caching_permissions = {'output': True}

    protocoles = {'GPIB': 'INSTR'}

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`.

        """
        super(Keithley6221, self).open_connection(**para)
        self.write_termination = '\n'
        self.read_termination = '\n'

    ### Output

    @instrument_property
    @secure_communication()
    def output(self):
        """Function setter

        """
        value = self.query('OUTP:STAT?')
        if value:
            return value
        else:
            raise InstrIOError('Keithley6221 : Failed to return output state')

    @output.setter
    @secure_communication()
    def output(self, value):
        self.write('OUTP:STAT {}'.format(value))
        res = self.query('OUTP:STAT?')
        if ((value=='ON' and res != '1') or (value=='OFF' and res != '0')):
            raise InstrIOError('Keithley6221: Failed to toggle output')

    ### DC Current amplitude

    @instrument_property
    @secure_communication()
    def current_amplitude(self):
        """Current amplitude getter method.

        """
        ampl_curr = self.query("SOUR:AMPL?")
        if ampl_curr:
            return float(ampl_curr)
        else:
            raise InstrIOError('Instrument did not return the WF amplitude')

    @current_amplitude.setter
    @secure_communication()
    def current_amplitude(self, value):
        """Current compliance setter method.

        """
        self.write(":SOUR:AMPL {}".format(value))
        feedback = self.query('SOUR:AMPL?')
        # to avoid floating point rouding
        if abs(float(feedback) - round(value, 12)) > 1e-12:
            raise InstrIOError(cleandoc('''Instrument did not set correctly 
                                        the WF amplitude'''))

    ### DC Compliance

    @instrument_property
    @secure_communication()
    def current_compliance(self):
        """Current compliance getter method.

        """
        lim_volt = self.query("SOUR:CURR:COMP?")
        if lim_volt:
            return float(lim_volt)
        else:
            raise InstrIOError('Instrument did not return a compliance value')

    @current_compliance.setter
    @secure_communication()
    def current_compliance(self, value):
        """Current compliance setter method.

        """
        self.write("SOUR:CURR:COMP {}".format(value))
        feedback = self.query('SOUR:CURR:COMP')
        # to avoid floating point rouding
        if abs(float(feedback) - round(value, 12)) > 1e-12:
            raise InstrIOError(cleandoc('''Instrument did not set correctly 
                                        the compliance'''))

    ### Waveform function

    @instrument_property
    @secure_communication()
    def waveform_function(self):
        """Waveform type getter method.

        """
        wave_func = self.query("SOUR:WAVE:FUNC?")
        if wave_func:
            return wave_func
        else:
            raise InstrIOError('Instrument did not return the WF type')

    @waveform_function.setter
    @secure_communication()
    def waveform_function(self, value):
        """Waveform type setter method.

        """
        self.check_name(value)
        self.write("SOUR:WAVE:FUNC {}".format(value))
        feedback = self.query('SOUR:WAVE:FUNC?')
        # to avoid floating point rouding
        if not(feedback.lower()==value.lower()):
            raise InstrIOError(cleandoc('''Instrument did not set correctly 
                                        the WF type'''))

    ### Waveform frequency

    @instrument_property
    @secure_communication()
    def waveform_frequency(self):
        """Waveform frequency getter method.

        """
        wave_freq = self.query("SOUR:WAVE:FREQ?")
        if wave_freq:
            return float(wave_freq)
        else:
            raise InstrIOError('Instrument did not return the WF freq')

    @waveform_frequency.setter
    @secure_communication()
    def waveform_frequency(self, value):
        """Waveform frequency setter method.

        """
        self.write("SOUR:WAVE:FREQ {}".format(value))
        feedback = self.query('SOUR:WAVE:FREQ?')
        # to avoid floating point rouding
        if abs(float(feedback) - round(value, 12)) > 1e-12:
            raise InstrIOError(cleandoc('Instrument did not set correctly '
                                        'the WF freq'))

    ### Waveform amplitude

    @instrument_property
    @secure_communication()
    def waveform_amplitude(self):
        """Waveform amplitude getter method.

        """
        wave_ampl = self.query("SOUR:WAVE:AMPL?")
        if wave_ampl:
            return float(wave_ampl)
        else:
            raise InstrIOError('Instrument did not return the WF amplitude')

    @waveform_frequency.setter
    @secure_communication()
    def waveform_amplitude(self, value):
        """Waveform amplitude setter method.

        """
        self.write("SOUR:WAVE:AMPL {}".format(value))
        feedback = self.query('SOUR:WAVE:AMPL?')
        # to avoid floating point rouding
        if abs(float(feedback) - round(value, 12)) > 1e-12:
            raise InstrIOError(cleandoc('''Instrument did not set correctly 
                                        the WF amplitude'''))

    ### Waveform offset

    @instrument_property
    @secure_communication()
    def waveform_offset(self):
        """Waveform offset getter method.

        """
        wave_off = self.query("SOUR:WAVE:OFFS?")
        if wave_off:
            return float(wave_off)
        else:
            raise InstrIOError('Instrument did not return the WF offset')

    @waveform_offset.setter
    @secure_communication()
    def waveform_offset(self, value):
        """Waveform offset setter method.

        """
        self.write("SOUR:WAVE:OFFS {}".format(value))
        feedback = self.query('SOUR:WAVE:OFFS?')
        # to avoid floating point rouding
        if abs(float(feedback) - round(value, 12)) > 1e-12:
            raise InstrIOError(cleandoc('''Instrument did not set correctly 
                                        the WF offset'''))

    ### Waveform cycles

    @instrument_property
    @secure_communication()
    def waveform_cycles(self):
        """Waveform cycles getter method.

        """
        wave_off = self.query("SOUR:WAVE:DUR:CYCL?")
        if wave_off:
            return float(wave_off)
        else:
            raise InstrIOError('Instrument did not return the WF cycles')

    @waveform_cycles.setter
    @secure_communication()
    def waveform_cycles(self, value):
        """Waveform cycles setter method.

        """
        self.write("SOUR:WAVE:DUR:CYCL {}".format(value))
        feedback = self.query('SOUR:WAVE:DUR:CYCL?')
        # to avoid floating point rouding
        if abs(float(feedback) - round(value, 12)) > 1e-12:
            raise InstrIOError(cleandoc('''Instrument did not set correctly 
                                        the WF cycles'''))

    def waveform_cycles_set_infinity(self):
        """ Set the waveform duration to infinity.
        """
        self.write("SOUR:WAVE:DUR:CYCL INF")
        feedback = self.query('SOUR:WAVE:DUR:CYCL?')
        if not (float(feedback) > 1e12):
            log = logging.getLogger(__name__)
            msg = ('Feedback is %s')
            log.info(msg,feedback)
            raise InstrIOError(cleandoc('Instrument did not set correctly '
                                        'the unlimited WF'))

    ### Waveform duty cycle

    @instrument_property
    @secure_communication()
    def waveform_duty(self):
        """Waveform duty cycle getter method.

        """
        wave_duty = self.query("SOUR:WAVE:DUR:DCYC?")
        if wave_duty:
            return float(wave_duty)/100.0
        else:
            raise InstrIOError('Instrument did not return the WF cycles')

    @waveform_duty.setter
    @secure_communication()
    def waveform_duty(self, value):
        """Waveform duty cycle setter method.

        """
        self.write("SOUR:WAVE:DUR:DCYC {}".format(100.0*value))
        feedback = self.query('SOUR:WAVE:DUR:DCYC?')
        # to avoid floating point rouding
        if abs(float(feedback) - round(100.0*value, 12)) > 1e-12:
            raise InstrIOError(cleandoc('''Instrument did not set correctly 
                                        the WF duty cycle'''))

    def check_name(self, value):
        if value not in {'SIN','RAMP','SQU','ARB1','ARB2','ARB3','ARB4'}:
            raise ValueError(cleandoc('''Waveform type for Keithley 6221  
                                         can only be SIN, RAMP, SQU, ARB1, 
                                         ARB2, ARB3, ARB4'''))

    def set_ac_waveform(self, waveform_function,
                              waveform_freq,
                              waveform_ampl,
                              waveform_offset,
                              waveform_duty,
                              waveform_finite,
                              waveform_cycles):
        """Sets the AC current waveform as required.

        """
        #avoid error when already on
        if not (self.waveform_function==waveform_function):
            self.waveform_function=waveform_function

        self.waveform_frequency=waveform_freq
        self.waveform_amplitude=waveform_ampl
        self.waveform_offset=waveform_offset
        if waveform_function in {'RAMP','SQU'}:
            self.waveform_duty=waveform_duty
        if self.query('OUTP:STAT?')=='1':
            log = logging.getLogger(__name__)
            msg = 'Keithley 6221 cannot update WF duration while on'
            log.warning(msg)
        else:
            if waveform_finite:
                self.waveform_cycles=waveform_cycles
            else:
                self.waveform_cycles_set_infinity()

    @secure_communication()
    def set_ac_output(self, switch):
        """Sets the AC output to the specified value: ON or OFF
        Arms the AC current waveform if required.

        """
        if switch == True:
            self.write('SOUR:WAVE:ARM')
            self.write('SOUR:WAVE:INIT')
        else:
            self.write('SOUR:WAVE:ABOR')

    @secure_communication()
    def check_connection(self):
        """Check wether or not a front panel user set the instrument in local.

        If a front panel user set the instrument in local the cache can be
        corrupted and should be cleared.

        """
        val = ('{0:08b}'.format(int(self.query('*ESR'))))[::-1]
        if val:
            return val[6]