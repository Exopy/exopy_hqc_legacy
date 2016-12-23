# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by EcpyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Driver for the Cryomagnetic superconducting magnet power supply CS4.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from inspect import cleandoc
from time import sleep

from ..driver_tools import (InstrIOError, secure_communication,
                            instrument_property)
from ..visa_tools import VisaInstrument


_GET_HEATER_DICT = {'0': 'Off',
                    '1': 'On'}

_ACTIVITY_DICT = {'To zero': 'SWEEP ZERO'}

OUT_FLUC = 2e-4
MAXITER = 10


class CS4(VisaInstrument):

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super(CS4, self).__init__(connection_info, caching_allowed,
                                  caching_permissions)
        try:
            mc = connection_info['magnet_conversion']
            self.field_current_ratio = float(mc)
        except KeyError:
            raise InstrIOError(cleandoc('''The field to current ratio
                 of the currently used magnet need to be specified in
                 the instrument settings. One should also check that
                 the switch heater current is correct.'''))

    @secure_communication()
    def make_ready(self):
        """Setup the correct unit and range.

        """
        self.write('UNITS T')
        self.write('RANGE 0 100')
        # we'll only use the command sweep up (ie to upper limit)
        # however upper limit can't be lower than lower limit for
        # some sources : G4 for example
        # set lower limit to lowest value
        self.write('LLIM -7')

    def go_to_field(self, value, rate, auto_stop_heater=True,
                    post_switch_wait=30):
        """Ramp up the field to the specified value.

        """
        # sweeping rate is converted from T/min to A/sec
        self.field_sweep_rate = rate / (60 * self.field_current_ratio)

        if abs(self.persistent_field - value) >= OUT_FLUC:

            if self.heater_state == 'Off':
                self.target_field = self.persistent_field
                self.heater_state = 'On'
                sleep(1)

            self.target_field = value

        if auto_stop_heater:
            self.heater_state = 'Off'
            sleep(post_switch_wait)
            self.activity = 'To zero'
            wait = abs(self.target_field) / self.field_sweep_rate
            wait /= FIELD_CURRENT_RATIO
            sleep(wait)
            niter = 0
            while abs(self.target_field) >= OUT_FLUC:
                sleep(5)
                niter += 1
                if niter > MAXITER:
                    raise InstrIOError(cleandoc('''CS4 didn't set the
                        field to zero after {} sec'''.format(5 * MAXITER)))

    def check_connection(self):
        pass

    @instrument_property
    def heater_state(self):
        """State of the switch heater allowing to inject current into the
        coil.

        """
        heat = self.ask('PSHTR?').strip()
        try:
            return _GET_HEATER_DICT[heat]
        except KeyError:
            raise ValueError(cleandoc('''The switch is in fault or
                                         absent'''))

    @heater_state.setter
    @secure_communication()
    def heater_state(self, state):
        if state in ['On', 'Off']:
            self.write('PSHTR {}'.format(state))

    @instrument_property
    def field_sweep_rate(self):
        """Rate at which to ramp the field.

        """
        return float(self.ask('RATE? 0'))

    @field_sweep_rate.setter
    @secure_communication()
    def field_sweep_rate(self, rate):
        self.write('RATE 0 {}'.format(rate))

    @instrument_property
    def fast_sweep_rate(self):
        """Rate at which to ramp the field when the switch heater is off.

        """
        return float(self.ask('RATE? 5'))

    @field_sweep_rate.setter
    @secure_communication()
    def fast_sweep_rate(self, rate):
        self.write('RATE 5 {}'.format(rate))

    @instrument_property
    def target_field(self):
        """Field that the source will try to reach.

        """
        return float(self.ask('IOUT?').strip(' T'))

    @target_field.setter
    @secure_communication()
    def target_field(self, target):
        """Sweep the output intensity to reach the specified ULIM (in A)
        at a rate depending on the intensity, as defined in the range(s).

        """
        self.write('ULIM {}'.format(target))

        if self.heater_state == 'Off':
            wait = abs(self.target_field - target) / self.fast_sweep_rate
            self.write('SWEEP UP FAST')
        else:
            wait = abs(self.target_field - target) / self.field_sweep_rate
            # careful, need to specify slow after a fast sweep !
            self.write('SWEEP UP SLOW')

        wait /= (60 * FIELD_CURRENT_RATIO)
        sleep(wait)
        niter = 0
        while abs(self.target_field - target) >= OUT_FLUC:
            sleep(5)
            niter += 1
            if niter > MAXITER:
                raise InstrIOError(cleandoc('''CS4 didn't set the field
                                               to {}'''.format(target)))


    @instrument_property
    def persistent_field(self):
        """Last known value of the magnet field.

        """
        return float(self.ask('IMAG?').strip(' T'))

    @instrument_property
    def activity(self):
        """Current activity of the power supply (idle, ramping).

        """
        return self.ask('SWEEP?').strip()

    @activity.setter
    @secure_communication()
    def activity(self, value):
        par = _ACTIVITY_DICT.get(value, None)
        if par:
            self.write(par)
        else:
            raise ValueError(cleandoc(''' Invalid parameter {} sent to
                             CS4 set_activity method'''.format(value)))
