# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task to set the parameters of microwave sources..

"""
import time
import numbers

from atom.api import (Float, Value, Str, Int, Bool, set_default, Enum, Tuple)

from exopy.tasks.api import (InstrumentTask, TaskInterface,
                            InterfaceableTaskMixin, validators)

class GetDCVoltageTask(InstrumentTask):
    """Get the current DC voltage of an instrument
    """

    parallel = set_default({'activated': False, 'pool': 'instr'})
    database_entries = set_default({'voltage': 0.01})

    def perform(self, value=None):
        """Default interface.

        """
        if self.driver.owner != self.name:
            self.driver.owner = self.name
            if hasattr(self.driver, 'function') and\
                    self.driver.function != 'VOLT':
                msg = ('Instrument assigned to task {} is not configured to '
                       'output a voltage')
                raise ValueError(msg.format(self.name))

        current_value = getattr(self.driver, 'voltage')
        self.write_in_database('voltage', float(current_value))


class SetDCVoltageTask(InterfaceableTaskMixin, InstrumentTask):
    """Set a DC voltage to the specified value.

    The user can choose to limit the rate by choosing an appropriate back step
    (larger step allowed), and a waiting time between each step.
    Also, the ramp can be done by the instrument itself according to 

    """
    #: Target value for the source (dynamically evaluated)
    target_value = Str().tag(pref=True, feval=validators.SkipLoop(types=numbers.Real))

    #: Largest allowed step when changing the output of the instr.
    back_step = Float().tag(pref=True)

    #: Largest allowed voltage
    safe_max = Float(0.0).tag(pref=True)

    #: Largest allowed delta compared to current voltage. 0 = ignored
    safe_delta = Float(0.0).tag(pref=True)

    #: Time to wait between changes of the output of the instr.
    delay = Float(0.01).tag(pref=True)

    #: Time to wait after setting voltage for source stabilisation
    stab_wait = Float(0.01).tag(pref=True)

    #: Whether to rely on internal instrument function for backstep and delay ramp
    ramp_with_instr = Bool(False).tag(pref=True)

    #: Whether to wait for source checking its output
    wait_instr_feedback = Bool(False).tag(pref=True)

    parallel = set_default({'activated': True, 'pool': 'instr'})
    database_entries = set_default({'voltage': 0.01 })

    def check_for_interruption(self):
        """Check if the user required an interruption.

        """
        return self.root.should_stop.is_set()

    def i_perform(self, value=None):
        """Default interface.

        """
        if self.driver.owner != self.name:
            self.driver.owner = self.name
            if hasattr(self.driver, 'function') and\
                    self.driver.function != 'VOLT':
                msg = ('Instrument assigned to task {} is not configured to '
                       'output a voltage')
                raise ValueError(msg.format(self.name))

        current_value = getattr(self.driver, 'voltage')

        value = self.format_and_eval_string(self.target_value)

        if self.safe_delta and abs(current_value-value) > self.safe_delta:
            msg = ('Voltage asked for {} is too far away from the current voltage {}!')
            raise ValueError(msg.format(value,current_value))

        if self.ramp_with_instr:
            success = self.instr_set(value, self.driver.smooth_change, current_value)
        else:    
            setter = lambda value: setattr(self.driver, 'voltage', value)
            success = self.smooth_set(value, setter, current_value)
        self.instr_wait()
        if success == True:
            if self.wait_instr_feedback:
                success == self.driver.without_errors()
        if success == False:
            raise InstrError(msg.format(self.name))
        

    def instr_set(self, target_value, setter, current_value):
        """ Smoothly set the voltage relying on instrument ramp.

        target_value : float
            Voltage to reach.

        setter : callable
            Function to set the voltage, should take as single argument the
            value.

        """
        if target_value is not None:
            value = target_value
        else:
            value = self.format_and_eval_string(self.target_value)

        if self.safe_max and self.safe_max < abs(value):
            msg = 'Requested voltage {} exceeds safe max : {}'
            raise ValueError(msg.format(value, self.safe_max))

        last_value = current_value
        normal_end = True

        if abs(last_value - value) < 1e-12:
            self.write_in_database('voltage', value)
            return True

        elif self.back_step == 0:
            msg = 'Requested backstep {} with ramp cannot be 0'
            raise ValueError(msg.format(self.back_step))

        elif self.delay == 0:
            msg = 'Requested delay {} with ramp cannot be 0'
            raise ValueError(msg.format(self.delay))

        if not self.root.should_stop.is_set():
            job = setter(last_value, value, self.back_step, self.delay)
            normal_end = job.wait_for_completion(self.check_for_interruption,
                                                 timeout=2,
                                                 refresh_time=0.1)
            if normal_end:
                self.driver.prev_target=value
                self.write_in_database('voltage', value)
                return True
            if not normal_end:
                job.cancel()
                return False
        
        self.write_in_database('voltage', last_value)
        return False

    def smooth_set(self, target_value, setter, current_value):
        """ Smoothly set the voltage.

        target_value : float
            Voltage to reach.

        setter : callable
            Function to set the voltage, should take as single argument the
            value.

        current_value: float
            Current voltage.

        """
        if target_value is not None:
            value = target_value
        else:
            value = self.format_and_eval_string(self.target_value)

        if self.safe_max and self.safe_max < abs(value):
            msg = 'Requested voltage {} exceeds safe max : {}'
            raise ValueError(msg.format(value, self.safe_max))

        last_value = current_value

        if abs(last_value - value) < 1e-12:
            self.write_in_database('voltage', value)
            return True

        elif self.back_step == 0:
            self.write_in_database('voltage', value)
            setter(value)
            return True

        else:
            if (value - last_value)/self.back_step > 0:
                step = self.back_step
            else:
                step = -self.back_step

        if abs(value-last_value) > abs(step):
            while not self.root.should_stop.is_set():
                # Avoid the accumulation of rounding errors
                last_value = round(last_value + step, 9)
                setter(last_value)
                time.sleep(self.delay)
                if not abs(value-last_value) > abs(step):
                    break

        if not self.root.should_stop.is_set():
            setter(value)
            self.write_in_database('voltage', value)
            return True

        self.write_in_database('voltage', last_value)
        return True

    def instr_wait(self):
        """ Implements stabilization wait

        """
        time.sleep(self.stab_wait)

class MultiChannelVoltageSourceInterface(TaskInterface):
    """Interface for multiple outputs sources.

    """
    #: Id of the channel to use.
    channel = Tuple(default=(1, 1)).tag(pref=True)

    #: Reference to the driver for the channel.
    channel_driver = Value()

    def perform(self, value=None):
        """Set the specified voltage.

        """
        task = self.task
        if not self.channel_driver:
            self.channel_driver = task.driver.get_channel(self.channel)
        if self.channel_driver.owner != task.name:
            self.channel_driver.owner = task.name
            if hasattr(self.channel_driver, 'function') and\
                    self.channel_driver.function != 'VOLT':
                msg = ('Instrument output assigned to task {} is not '
                       'configured to output a voltage')
                raise ValueError(msg.format(self.name))
        current_value = getattr(self.channel_driver, 'voltage')
        if task.ramp_with_instr:
            success = task.instr_set(value, self.channel_driver.smooth_change, current_value)
        else:    
            setter = lambda value: setattr(self.channel_driver, 'voltage', value)
            success = task.smooth_set(value, setter, current_value)
        task.instr_wait()
        if success == True:
            if task.wait_instr_feedback:
                success == self.channel_driver.without_errors()
        if success == False:
            raise InstrError('Task did not complete')

    def check(self, *args, **kwargs):
        if kwargs.get('test_instr'):
            task = self.task
            traceback = {}
            with task.test_driver() as d:
                if d is None:
                    return True, {}
                if self.channel not in d.defined_channels:
                    key = task.get_error_path() + '_interface'
                    traceback[key] = 'Missing channel {}'.format(self.channel)

            if traceback:
                return False, traceback
            else:
                return True, traceback

        else:
            return True, {}


class SetDCCurrentComplianceTask(InterfaceableTaskMixin, InstrumentTask):
    """Set a DC current compliance to the specified value.

    The user can choose to limit the value by a safety max

    """
    #: Target value for the compliance
    target_value = Str().tag(pref=True, feval=validators.SkipLoop(types=numbers.Real))

    #: Largest allowed current
    safe_max = Float(0.0).tag(pref=True)

    parallel = set_default({'activated': True, 'pool': 'instr'})
    database_entries = set_default({'compliance_value': 0.01})

    def i_perform(self, value=None):
        """Default interface.

        """
        if value is None:
            value = self.format_and_eval_string(self.target_value)

        if self.safe_max and self.safe_max < abs(value):
            msg = 'Requested current {} exceeds safe max : {}'
            raise ValueError(msg.format(value, self.safe_max))

        self.driver.current_compliance = value
        self.write_in_database('compliance_value', value)

class SetDCCurrentTask(InterfaceableTaskMixin, InstrumentTask):
    """Set a DC current to the specified value.

    The user can choose to limit the rate by choosing an appropriate back step
    (larger step allowed), and a waiting time between each step.

    """
    #: Target value for the source (dynamically evaluated)
    target_value = Str().tag(pref=True, feval=validators.SkipLoop(types=numbers.Real))

    #: Largest allowed step when changing the output of the instr.
    back_step = Float().tag(pref=True)

    #: Largest allowed current
    safe_max = Float(0.0).tag(pref=True)

    #: Time to wait between changes of the output of the instr.
    delay = Float(0.01).tag(pref=True)

    #: Time to wait after setting current for source stabilisation
    stab_wait = Float(0.01).tag(pref=True)

    parallel = set_default({'activated': True, 'pool': 'instr'})
    database_entries = set_default({'current': 0.01})

    def i_perform(self, value=None):
        """Default interface.

        """
        if self.driver.owner != self.name:
            self.driver.owner = self.name
            if hasattr(self.driver, 'function') and\
                    self.driver.function != 'CURR':
                msg = ('Instrument assigned to task {} is not configured to '
                       'output a current')
                raise ValueError(msg.format(self.name))

        setter = lambda value: setattr(self.driver, 'current', value)
        current_value = getattr(self.driver, 'current')

        self.smooth_set(value, setter, current_value)

    def smooth_set(self, target_value, setter, current_value):
        """ Smoothly set the current.

        target_value : float
            Current to reach.

        setter : callable
            Function to set the current, should take as single argument the
            value.

        """
        if target_value is not None:
            value = target_value
        else:
            value = self.format_and_eval_string(self.target_value)

        if self.safe_max and self.safe_max < abs(value):
            msg = 'Requested current {} exceeds safe max : {}'
            raise ValueError(msg.format(value, self.safe_max))

        last_value = current_value

        if abs(last_value - value) < 1e-9:
            self.write_in_database('current', value)
            return

        elif self.back_step == 0:
            self.write_in_database('current', value)
            setter(value)
            return

        else:
            if (value - last_value)/self.back_step > 0:
                step = self.back_step
            else:
                step = -self.back_step

        if abs(value-last_value) > abs(step):
            while not self.root.should_stop.is_set():
                # Avoid the accumulation of rounding errors
                last_value = round(last_value + step, 6)
                setter(last_value)
                if abs(value-last_value) > abs(step):
                    time.sleep(self.delay)
                else:
                    break

        if not self.root.should_stop.is_set():
            setter(value)
            self.write_in_database('current', value)
            return

        self.write_in_database('current', last_value)
        time.sleep(self.stab_wait)


class SetDCFunctionTask(InterfaceableTaskMixin, InstrumentTask):
    """Set a DC source function to the specified value: VOLT or CURR

    """
    #: Target value for the source (dynamically evaluated)
    switch = Str('VOLT').tag(pref=True, feval=validators.SkipLoop())

    database_entries = set_default({'function': 'VOLT'})

    def i_perform(self, switch=None):
        """Default interface.

        """
        if switch is None:
            switch = self.format_and_eval_string(self.switch)

        if switch == 'VOLT':
            self.driver.function = 'VOLT'
            self.write_in_database('function', 'VOLT')

        if switch == 'CURR':
            self.driver.function = 'CURR'
            self.write_in_database('function', 'CURR')


class SetDCOutputTask(InterfaceableTaskMixin, InstrumentTask):
    """Set a DC source output to the specified value: ON or OFF

    """
    #: Target value for the source output
    switch = Str('OFF').tag(pref=True, feval=validators.SkipLoop())

    database_entries = set_default({'output': "'OFF'"})

    def i_perform(self, switch=None):
        """Default interface.

        """
        if self.switch == "'ON'":
            self.driver.output = 'ON'
            self.write_in_database('output', "'ON'")

        elif self.switch == "'OFF'":
            self.driver.output = 'OFF'
            self.write_in_database('output', "'OFF'")
