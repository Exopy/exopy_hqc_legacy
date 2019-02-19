# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tests for the ApplyMagFieldTask

"""
from multiprocessing import Event

import pytest
import enaml

from exopy.tasks.api import RootTask
from exopy.tasks.tasks.logic.loop_task import LoopTask
from exopy.testing.util import show_and_close_widget
from exopy_hqc_legacy.tasks.tasks.instr.dc_tasks\
    import (SetDCVoltageTask, MultiChannelVoltageSourceInterface)

with enaml.imports():
    from exopy.tasks.tasks.logic.views.loop_view import LoopView
    from exopy_hqc_legacy.tasks.tasks.instr.views.dc_views\
        import SetDcVoltageView

from .instr_helper import InstrHelper, InstrHelperStarter, PROFILES, DRIVERS


class TestSetDCVoltageTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SetDCVoltageTask(name='Test')
        self.task.back_step = 0.1
        self.task.delay = 0.1
        self.root.add_child_task(0, self.task)

        self.root.run_time[DRIVERS] = {'Test': (InstrHelper,
                                                InstrHelperStarter())}
        self.root.run_time[PROFILES] =\
            {'Test1': {'connections': {'C': {'owner': []}},
                       'settings': {'S': {'check_connection': [True]}}
                       }
             }

        # This is set simply to make sure the test of InstrTask pass.
        self.task.selected_instrument = ('Test1', 'Test', 'C', 'S')

    def test_check_base_interface1(self):
        """Simply test that everything is ok if voltage can be evaluated.

        """
        self.task.target_value = '1.0'

        test, traceback = self.task.check(test_instr=True)
        assert test
        assert not traceback

    def test_check_base_interface2(self):
        """Check handling a wrong voltage.

        """
        self.task.target_value = '*1.0*'

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1

    def test_check_multichannel_interface1(self):
        """Check the multichannel specific tests, passing.

        """
        interface = MultiChannelVoltageSourceInterface(task=self.task)
        interface.channel = (1, 1)
        self.task.interface = interface
        self.task.target_value = '1.0'

        c = self.root.run_time[PROFILES]['Test1']['connections']
        c['C'] = {'defined_channels': [[1]]}

        test, traceback = self.task.check(test_instr=True)
        assert test
        assert not traceback

    def test_check_multichannel_interface2(self):
        """Check the multichannel specific tests, failing = driver.

        """
        interface = MultiChannelVoltageSourceInterface(task=self.task)
        interface.channel = (1, 1)
        self.task.interface = interface
        self.task.target_value = '1.0'

        self.root.run_time[DRIVERS] = {}
        c = self.root.run_time[PROFILES]['Test1']['connections']
        c['C'] = {'defined_channels': [[1]]}

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1

    def test_check_multichannel_interface3(self):
        """Check the multichannel specific tests, failing = profile.

        """
        interface = MultiChannelVoltageSourceInterface(task=self.task)
        interface.channel = (1, 1)
        self.task.interface = interface
        self.task.target_value = '1.0'
        self.task.selected_instrument = ()

        test, traceback = self.task.check()
        assert not test
        assert len(traceback) == 1

    def test_check_multichannel_interface4(self):
        """Check the multichannel specific tests, failing = channel.

        """
        interface = MultiChannelVoltageSourceInterface(task=self.task)
        interface.channel = (2, 1)
        self.task.interface = interface
        self.task.target_value = '1.0'

        c = self.root.run_time[PROFILES]['Test1']['connections']
        c['C'] = {'defined_channels': [[1]]}

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1

    def test_smooth_set_stopping(self):
        """Test stopping in the middle of a smooth stepping.

        """
        c = self.root.run_time[PROFILES]['Test1']['connections']
        c['C'] = {'voltage': [0.0], 'funtion': ['VOLT'], 'owner': [None]}

        self.root.prepare()
        self.root.should_stop.set()

        setter = lambda value: setattr(self.driver, 'voltage', value)

        self.task.smooth_set(1.0, setter, 0.0)
        assert self.root.get_from_database('Test_voltage') == 0.0

    def test_perform_base_interface(self):
        """Test also that a target which is not a multiple of the back step
        is correctly handled.

        """
        self.task.target_value = '0.05'

        c = self.root.run_time[PROFILES]['Test1']['connections']
        c['C'] = {'voltage': [0.0], 'funtion': ['VOLT'], 'owner': [None]}

        self.root.prepare()

        self.task.perform()
        assert self.root.get_from_database('Test_voltage') == 0.05
        self.task.target_value = '1.06'
        self.task.perform()
        assert self.root.get_from_database('Test_voltage') == 1.06

    def test_perform_multichannel_interface(self):
        """Test using the interface for the setting.

        """
        interface = MultiChannelVoltageSourceInterface(task=self.task)
        interface.channel = (1, 1)
        self.task.interface = interface
        self.task.target_value = '1.0'

        c = self.root.run_time[PROFILES]['Test1']['connections']
        c['C'] = {'voltage': [0.0], 'funtion': ['VOLT'], 'owner': [None]}
        s = self.root.run_time[PROFILES]['Test1']['settings']
        s['S'] = {'get_channel': lambda x, i: x}

        self.root.prepare()
        self.task.perform()
        assert self.root.get_from_database('Test_voltage') == 1.0


@pytest.mark.ui
def test_set_dc_voltage_view(exopy_qtbot, root_view, task_workbench):
    """Test SetDCVoltageView widget outisde of a LoopTask.

    """
    task = SetDCVoltageTask(name='Test')
    root_view.task.add_child_task(0, task)
    show_and_close_widget(exopy_qtbot, SetDcVoltageView(task=task, root=root_view))


@pytest.mark.ui
def test_set_dc_voltage_view2(exopy_qtbot, root_view, task_workbench):
    """Test SetDCVoltageView widget inside of a LoopTask.

    """
    task = SetDCVoltageTask(name='Test')
    interface = MultiChannelVoltageSourceInterface(task=task)
    task.interface = interface
    loop = LoopTask(name='r', task=task)
    root_view.task.add_child_task(0, loop)
    # XXX check for absence of target field
    show_and_close_widget(exopy_qtbot, LoopView(task=loop, root=root_view))
