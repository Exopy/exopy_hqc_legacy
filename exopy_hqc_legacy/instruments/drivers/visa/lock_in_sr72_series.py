# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Drivers for lock-in from Signal Recovery using VISA library.

"""
from ..driver_tools import (InstrIOError, secure_communication)
from ..visa_tools import VisaInstrument
import numpy as np
import logging


class LockInSR7265(VisaInstrument):
    """Driver for a SR7265 lock-in, using the VISA library.

    This driver does not give access to all the functionnality of the
    instrument but you can extend it if needed. See the documentation of the
    driver_tools package for more details about writing instruments drivers.

    Parameters
    ----------
    see the `VisaInstrument` parameters in the `driver_tools` module

    Methods
    -------
    read_x()
        Return the x quadrature measured by the instrument
    read_y()
        Return the y quadrature measured by the instrument
    read_xy()
        Return the x and y quadratures measured by the instrument
    read_amplitude()
        Return the ammlitude of the signal measured by the instrument
    read_phase()
        Return the phase of the signal measured by the instrument
    read_amp_and_phase()
        Return the amplitude and phase of the signal measured by the instrument
    read_x_stddev()
        Return the x quadrature standard deviation measured by the instrument
    read_y_stddev()
        Return the y quadrature standard deviation measured by the instrument

    Notes
    -----
    The completion of each command is checked by reading the status byte (see
    `_check_status` method)

    """

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`.

        """
        super(LockInSR7265, self).open_connection(**para)
        self.write_termination = '\n'
        self.read_termination = '\n'

    def query_safewhenzero(self, SCPIInstr):
        """This query method avoids issues with strings of type 0.0E+00\x00\r

        """
        try:
            res = self.query(SCPIInstr)
            value = float(res)
        except ValueError:
            value = 0
        return value

    def query_ascii_values_safewhenzero(self, SCPIInstr):
        """This query method avoids issues with strings of type 0.0E+00\x00\r

        """
        try:
            res = self.query_ascii_values(SCPIInstr)
            values = tuple([float(r) for r in res])
        except ValueError:
            values = 0,0
        return values

    @secure_communication()
    def read_x(self):
        """
        Return the x quadrature measured by the instrument

        Perform a direct reading without any waiting. Can return non
        independent values if the instrument is queried too often.

        """
        value = self.query_safewhenzero('X.')
        status = self._check_status()
        if status != 'OK' or not value:
            raise InstrIOError('The command did not complete correctly')
        else:
            return value

    @secure_communication()
    def read_y(self):
        """
        Return the y quadrature measured by the instrument

        Perform a direct reading without any waiting. Can return non
        independent values if the instrument is queried too often.

        """
        value = self.query_safewhenzero('Y.')
        status = self._check_status()
        if status != 'OK' or not value:
            raise InstrIOError('The command did not complete correctly')
        else:
            return value

    @secure_communication()
    def read_xy(self):
        """
        Return the x and y quadratures measured by the instrument

        Perform a direct reading without any waiting. Can return non
        independent values if the instrument is queried too often.

        """
        values = self.query_ascii_values_safewhenzero('XY.')
        status = self._check_status()
        if status != 'OK' or not values:
            raise InstrIOError('The command did not complete correctly')
        else:
            return values

    @secure_communication()
    def read_amplitude(self):
        """
        Return the amplitude of the signal measured by the instrument

        Perform a direct reading without any waiting. Can return non
        independent values if the instrument is queried too often.

        """
        value = self.query_safewhenzero('MAG.')
        status = self._check_status()
        if status != 'OK' or not value:
            return InstrIOError('The command did not complete correctly')
        else:
            return value

    @secure_communication()
    def read_phase(self):
        """
        Return the phase of the signal measured by the instrument

        Perform a direct reading without any waiting. Can return non
        independent values if the instrument is queried too often.

        """
        value = self.query_safewhenzero('PHA.')
        status = self._check_status()
        if status != 'OK' or not value:
            raise InstrIOError('The command did not complete correctly')
        else:
            return value

    @secure_communication()
    def read_amp_and_phase(self):
        """
        Return the amplitude and phase of the signal measured by the instrument

        Perform a direct reading without any waiting. Can return non
        independent values if the instrument is queried too often.

        """
        values = self.query_ascii_values_safewhenzero('MP.')
        status = self._check_status()
        if status != 'OK' or not values:
            raise InstrIOError('The command did not complete correctly')
        else:
            return values

    @secure_communication()
    def read_xstddev(self):
        """
        Not implemented

        """
        raise RuntimeError('This command is not yet implemented'
                           'for the instrument')

    @secure_communication()
    def read_ystddev(self):
        """
        Not implemented

        """
        raise RuntimeError('This command is not yet implemented'
                           'for the instrument')

    @secure_communication()
    def set_osc_frequency(self, frequency):
        """
        Set the frequency (in Hz) outputted by the instrument

        """
        log = logging.getLogger(__name__)
        msg = ('Set oscillation frequency (instr prop) to {:e}Hz'.format(frequency))
        log.info(msg)
        odg = np.floor(np.log10(frequency))
        int_part = np.round(frequency/10**odg, 8)
        self.write('OF. {}E{}'.format(int_part,odg))
        status = self._check_status()
        value = self.query_safewhenzero('OF.')
        if np.abs(frequency-value)>1e-9:
            raise InstrIOError('The instrument did not set frequency correctly')
        if status != 'OK':
            raise InstrIOError('The command did not complete correctly')

    @secure_communication()
    def set_out_amplitude(self, amplitude):
        """
        Set the amplitude (in mV) outputted by the instrument

        """
        log = logging.getLogger(__name__)
        msg = ('Set oscillation amplitude (instr prop) to {:e}mV'.format(amplitude))
        log.info(msg)
        self.write('OA. {}E-3'.format(int(amplitude)))
        status = self._check_status()
        value = self.query_safewhenzero('OA.')
        log.info(value)
        if np.abs(amplitude*1e-3 - value) > 1e-9:
            raise InstrIOError('The instrument did not set amplitude correctly')
        if status != 'OK':
            raise InstrIOError('The command did not complete correctly')

    @secure_communication()
    def _check_status(self):
        """
        Read the value of the status byte to determine if the last command
        executed properly
        """
        bites = self.query('ST')
        status_byte = ('{0:08b}'.format(ord(bites[0])))[::-1]
        if not status_byte[0]:
            return 'Command went wrong'
        else:
            return 'OK'


class LockInSR7270(LockInSR7265):
    """
    Driver for a SR7270 lock-in, using the VISA library.

    This driver does not give access to all the functionnality of the
    instrument but you can extend it if needed. See the documentation of the
    driver_tools package for more details about writing instruments drivers.

    Parameters
    ----------
    see the `VisaInstrument` parameters in the `driver_tools` module

    Methods
    -------
    read_x()
        Return the x quadrature measured by the instrument
    read_y()
        Return the y quadrature measured by the instrument
    read_xy()
        Return the x and y quadratures measured by the instrument
    read_amplitude()
        Return the ammlitude of the signal measured by the instrument
    read_phase()
        Return the phase of the signal measured by the instrument
    read_amp_and_phase()
        Return the amplitude and phase of the signal measured by the instrument

    Notes
    -----
    The completion of each command is checked by reading the status byte (see
    `_check_completion` method).
    The only difference between this driver and the one for the SR7265 is the
    termination character used and the fact that the SR7270 automatically
    return the status byte.

    """

    def __init__(self, *args, **kwargs):

        super(LockInSR7270, self).__init__(*args, **kwargs)
        self.write_termination = '\0'
        self.read_termination = '\0'

    @secure_communication()
    def _check_status(self):
        """
        Read the value of the status byte to determine if the last command
        executed properly
        """
        bites = self.read()
        status_byte = ('{0:08b}'.format(ord(bites[0])))[::-1]
        if not status_byte[0]:
            return 'Command went wrong'
        else:
            return 'OK'

class LockInSR7280(LockInSR7265):
    """
    Driver for a SR7270 lock-in, using the VISA library.

    This driver does not give access to all the functionnality of the
    instrument but you can extend it if needed. See the documentation of the
    driver_tools package for more details about writing instruments drivers.

    In principle, no difference between 7265 and 7280.
    """

    def __init__(self, *args, **kwargs):

        super(LockInSR7280, self).__init__(*args, **kwargs)
        self.write_termination = '\n'
        self.read_termination = '\n'
