# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2022 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Drivers for Lakeshore Hall probe system using VISA library.
"""
from ..driver_tools import (InstrIOError, secure_communication)
from ..visa_tools import VisaInstrument

import numpy as np

class LakeShore475(VisaInstrument):
    """Driver for a LakeShore Model 475 gaussmeter, using the VISA library.
    This driver does not give access to all the functionnality of the
    instrument but you can extend it if needed. See the documentation of the
    driver_tools package for more details about writing instruments drivers.
    Parameters
    ----------
    see the `VisaInstrument` parameters in the `driver_tools` module
    Methods
    -------
    read_temperature()
        Return the temperature measured by the instrument
    read_field()
        Return the magnetic field measured by the instrument
    Notes
    -----

    """

    LOWPASS_AVAILABLE=[20, 60, 140]
    WIDEBANDPASS_AVAILABLE=[100, 200, 400, 800, 1600, 3200, 6400, 0]

    def open_connection(self, **para):
        """Open the connection to the instr using the `connection_str`.
        """
        super(LakeShore475, self).open_connection(**para)
        self.write_termination = '\n'
        self.read_termination = '\n'

    @secure_communication()
    def setup_dc(self):
        self.write('RST; RDGMODE 1,6,1,1,1; AUTO 1; UNIT 2; *OPC?')

    @secure_communication()
    def setup_ac(self,filterLP,filterWB):
        if filterLP:
            filt_values = np.asarray(self.LOWPASS_AVAILABLE)
            idx = (np.abs(filt_values - filterLP)).argmin()
            self.write('RST; RDGMODE 2,3,3,1,1; FILTER 8,1,{}; AUTO 0; RANGE 2; UNIT 2; *OPC?'.format(idx+1))
        elif filterWB:
            filt_values = np.asarray(self.WIDEBANDPASS_AVAILABLE)
            idx = (np.abs(filt_values - filterWB)).argmin()
            self.write('RST; RDGMODE 2,3,1,1,1; FILTER {},1,3; AUTO 0; RANGE 2; UNIT 2; *OPC?'.format(idx+1))
        else:
            self.write('RST; RDGMODE 2,3,1,1,1; FILTER 8,1,3; AUTO 0; RANGE 2; UNIT 2; *OPC?')

    @secure_communication()
    def read_temperature(self):
        """
        Return the temperature for the probe measured by the instrument
        """
        value = self.query('RDGTEMP?')
        
        return float(value)

    @secure_communication()
    def read_field(self):
        """
        Return the field for the probe measured by the instrument
        """
        value = self.query('RDGFIELD?')

        return float(value)

    @secure_communication()
    def read_freq(self):
        """
        Return the field for the probe measured by the instrument
        """
        value = self.query('RDGFRQ?')
        
        return float(value)