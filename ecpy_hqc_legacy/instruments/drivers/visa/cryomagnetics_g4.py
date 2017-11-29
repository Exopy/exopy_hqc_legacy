# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by EcpyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Driver for the Cryomagnetic superconducting magnet power supply 4G.
It is very close to the CS4 one but for a few bugs in the software:
- even though units is set to T, the fields are returned in kG
- some instructions need a semicolon at their end to be taken into account
(namely ULIM and RATE)

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from inspect import cleandoc
from time import sleep

from ..driver_tools import (InstrIOError, secure_communication,
                            instrument_property)
from ..visa_tools import VisaInstrument
from .cryomagnetics_cs4 import CS4
# TODO: check that sweep fast works...
# it does but the fast_sweep_rate is not correctly given

class C4G(CS4):

    @secure_communication()
    def make_ready(self):
    	""" Setting the used range to the whole current range

    	"""
    	self.write('RANGE 0 100;')
    	super(C4G, self).make_ready()

    @instrument_property
    def out_field(self):
        """Field that the source will try to reach, in T.
        Iout is given in kG.

        """
        return float(self.ask('IOUT?').strip('kG')) / 10

    @out_field.setter
    @secure_communication()
    def out_field(self, target):
        """Sweep the output intensity to reach the specified ULIM (in A)
        at a rate depending on the intensity, as defined in the range(s).

        """
        # convert target field from T to kG
        self.write('ULIM {}'.format(target * 10))
        if self.heater_state == 'Off':
            self.write('SWEEP UP FAST')
        else:
            # need to specify slow in case there was a fast sweep before
            self.write('SWEEP UP SLOW')

    @instrument_property
    def persistent_field(self):
        """Last known value of the magnet field, in T.

        """
        print(self.ask('IMAG?'))
        return float(self.ask('IMAG?').strip('kG')) / 10

    @instrument_property
    def field_sweep_rate(self):
        """Rate at which to ramp the field (T/min).

        """
        # converted from A/s to T/min
        rate = float(self.ask('RATE? 0'))
        return rate * (60 * self.field_current_ratio)

    @field_sweep_rate.setter
    @secure_communication()
    def field_sweep_rate(self, rate):
        # converted from T/min to A/s
        rate /= 60 * self.field_current_ratio
        self.write('RATE 0 {};'.format(rate))
        
    @instrument_property
    def fast_sweep_rate(self):
        """Rate at which to ramp the field when the switch heater is off
        (T/min).

        """
        print('evaluating rate in g4')
        rate = float(self.ask('RATE? 5'))
        return rate * (60 * self.field_current_ratio)

    @field_sweep_rate.setter
    @secure_communication()
    def fast_sweep_rate(self, rate):
        rate /= 60 * self.field_current_ratio
        self.write('RATE 5 {}'.format(rate))