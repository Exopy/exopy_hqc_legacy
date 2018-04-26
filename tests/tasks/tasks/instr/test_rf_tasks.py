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
from exopy_hqc_legacy.tasks.tasks.instr.rf_tasks\
    import (SetRFFrequencyTask, SetRFPowerTask, SetRFOnOffTask)

with enaml.imports():
    from exopy.tasks.tasks.logic.views.loop_view import LoopView
    from exopy_hqc_legacy.tasks.tasks.instr.views.rf_views\
        import (RFFrequencyView, RFPowerView, RFSetOnOffView)

from .instr_helper import InstrHelper, InstrHelperStarter, PROFILES, DRIVERS


class TestSetRFFrequencyTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SetRFFrequencyTask(name='Test')
        self.task.unit = 'GHz'
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
        self.task.frequency = '1.0'

        test, traceback = self.task.check(test_instr=True)
        assert test
        assert not traceback

    def test_check_base_interface2(self):
        # Check handling a wrong frequency.
        self.task.frequency = '*1.0*'

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1

    def test_perform_base_interface(self):
        self.task.frequency = '1.0'

        c = self.root.run_time[PROFILES]['Test1']['connections']
        c['C'] = {'frequency': [0.0], 'frequency_unit': ['GHz'],
                  'owner': [None]}
        self.root.prepare()

        self.task.perform()
        assert self.root.get_from_database('Test_frequency') == 1.0


@pytest.mark.ui
def test_rf_frequency_view(exopy_qtbot, root_view, task_workbench):
    """Test SetRFFrequencyTask widget outisde of a LoopTask.

    """
    task = SetRFFrequencyTask(name='Test')
    root_view.task.add_child_task(0, task)
    show_and_close_widget(exopy_qtbot, RFFrequencyView(task=task, root=root_view))


@pytest.mark.ui
def test_rf_frequency_view2(exopy_qtbot, root_view, task_workbench):
    """Test SetRFFrequencyTask widget inside of a LoopTask.

    """
    task = SetRFFrequencyTask(name='Test')
    loop = LoopTask(name='r', task=task)
    root_view.task.add_child_task(0, loop)
    # XXX check for absence of target field
    show_and_close_widget(exopy_qtbot, LoopView(task=loop, root=root_view))


class TestSetRFPowerTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SetRFPowerTask(name='Test')
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
        # Simply test that everything is ok if voltage can be evaluated.
        self.task.power = '1.0'

        test, traceback = self.task.check(test_instr=True)
        assert test
        assert not traceback

    def test_check_base_interface2(self):
        # Check handling a wrong power.
        self.task.power = '*1.0*'

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1

    def test_perform_base_interface(self):
        self.task.power = '1.0'

        c = self.root.run_time[PROFILES]['Test1']['connections']
        c['C'] = {'power': [0.0], 'owner': [None]}
        self.root.prepare()

        self.task.perform()
        assert self.root.get_from_database('Test_power') == 1.0


@pytest.mark.ui
def test_rf_power_view(exopy_qtbot, root_view, task_workbench):
    """Test RFPowerView widget outisde of a LoopTask.

    """
    task = SetRFPowerTask(name='Test')
    root_view.task.add_child_task(0, task)
    show_and_close_widget(exopy_qtbot, RFPowerView(task=task, root=root_view))


@pytest.mark.ui
def test_rf_power_view2(exopy_qtbot, root_view, task_workbench):
    """Test RFPowerView widget inside of a LoopTask.

    """
    task = SetRFPowerTask(name='Test')
    loop = LoopTask(name='r', task=task)
    root_view.task.add_child_task(0, loop)
    # XXX check for absence of target field
    show_and_close_widget(exopy_qtbot, LoopView(task=loop, root=root_view))


class TestSetRFOnOffTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SetRFOnOffTask(name='Test')
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
        # Simply test that everything is ok if voltage can be evaluated.
        self.task.switch = '1.0'

        test, traceback = self.task.check(test_instr=True)
        assert test
        assert not traceback

    def test_check_base_interface2(self):
        # Check handling a wrong voltage.
        self.task.switch = '*1.0*'

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1

    def test_perform_base_interface(self):
        self.task.switch = '1.0'

        c = self.root.run_time[PROFILES]['Test1']['connections']
        c['C'] = {'output': [0.0], 'owner': [None]}
        self.root.prepare()

        self.task.perform()
        assert self.root.get_from_database('Test_output') == 1.0


@pytest.mark.ui
def test_rf_output_view(exopy_qtbot, root_view, task_workbench):
    """Test RFSetOnOffView widget outisde of a LoopTask.

    """
    task = SetRFOnOffTask(name='Test')
    root_view.task.add_child_task(0, task)
    show_and_close_widget(exopy_qtbot, RFSetOnOffView(task=task, root=root_view))


@pytest.mark.ui
def test_rf_output_view2(exopy_qtbot, root_view, task_workbench):
    """Test RFSetOnOffView widget inside of a LoopTask.

    """
    task = SetRFOnOffTask(name='Test')
    loop = LoopTask(name='r', task=task)
    root_view.task.add_child_task(0, loop)
    # XXX check for absence of target field
    show_and_close_widget(exopy_qtbot, LoopView(task=loop, root=root_view))
