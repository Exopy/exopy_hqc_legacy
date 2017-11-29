# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Driver for the Cryomagnetic superconducting magnet power supply CS4.

"""
from inspect import cleandoc
from time import sleep
from collections import OrderedDict

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

    def open_connection(self, **para):
        super(CS4, self).open_connection(**para)
        if not para:
            self.write_termination = '\n'
            self.read_termination = '\n'

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

    def evaluate_state(self, value):
        """Evaluate if a sweep in needed, and if the heater need to be
        turned on.
        """
        sw_needed = (abs(self.persistent_field - value) >= OUT_FLUC)
        state = OrderedDict()
        state['sw_needed'] = sw_needed 
        state['heater_off'] = self.heater_state == 'Off'
        return state.values()

    def check_success(self, target, time):
        """Check that the magnetic field is at target value.
        """
        niter = 0
        while abs(self.out_field - target) >= OUT_FLUC:
            sleep(5)
            niter += 1
            if niter > MAXITER:
                raise InstrIOError(cleandoc('''CS4 didn't set the field 
                      to {} after {} sec'''.format(target, 
                      time + 5 * MAXITER)))

    def prepare_heater_on(self):
        """
        """
        # heater off: fast sweep rate
        span = abs(self.out_field - self.persistent_field)
        self.out_field = self.persistent_field
        return (self.persistent_field, span, self.fast_sweep_rate)

    def heater_on(self):
        """Turn heater on.
        """
        self.heater_state = 'On'
        sleep(1)

    def go_to_field(self, value, rate):
        """Ramp up the field to the specified value.

        """
        # heater on: "slow" (specified) sweep rate
        self.field_sweep_rate = rate
        span = abs(self.out_field - value)
        self.out_field = value
        return (value, span, rate)


    def stop_heater(self, post_switch_wait):
        """Stop heater and sweep out field to 0.
        """
        # heater off: fast swep rate
        self.heater_state = 'Off'
        sleep(post_switch_wait)
        sw_span = abs(self.out_field)
        self.out_field = 0.
        print('fast sweep rate', self.fast_sweep_rate)
        return 0., sw_span, self.fast_sweep_rate


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
        self.write('RATE 0 {}'.format(rate))

    @instrument_property
    def fast_sweep_rate(self):
        """Rate at which to ramp the field when the switch heater is off
        (T/min).

        """
        print('evaluating rate')
        rate = float(self.ask('RATE? 5'))
        return rate * (60 * self.field_current_ratio)

    @fast_sweep_rate.setter
    @secure_communication()
    def fast_sweep_rate(self, rate):
        rate /= 60 * self.field_current_ratio
        self.write('RATE 5 {}'.format(rate))

    @instrument_property
    def out_field(self):
        """Field that the source will try to reach.

        """
        # in T
        return float(self.ask('IOUT?').strip(' T'))

    @out_field.setter
    @secure_communication()
    def out_field(self, target):
        """Sweep the output intensity to reach the specified ULIM (in T)
        at a rate depending on the intensity, as defined in the range(s).

        """
        self.write('ULIM {}'.format(target))
        if self.heater_state == 'Off':
            self.write('SWEEP UP FAST')
        else:
            # need to specify slow in case there was a fast sweep before
            self.write('SWEEP UP SLOW')

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
