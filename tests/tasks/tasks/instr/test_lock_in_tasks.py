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
from exopy.testing.util import show_and_close_widget
from exopy_hqc_legacy.tasks.tasks.instr.lock_in_measure_task\
    import LockInMeasureTask

with enaml.imports():
    from exopy_hqc_legacy.tasks.tasks.instr.views.lock_in_meas_view\
        import LockInMeasView

from .instr_helper import InstrHelper, InstrHelperStarter, PROFILES, DRIVERS


class TestLockInMeasureTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = LockInMeasureTask(name='Test')
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

    def test_mode_observation(self):
        """Check database is correctly updated when the mode change.

        """
        self.task.mode = 'X'

        assert self.task.get_from_database('Test_x') == 1.0
        aux = self.task.list_accessible_database_entries()
        assert 'Test_y' not in aux
        assert 'Test_amplitude' not in aux
        assert 'Test_phase' not in aux

        self.task.mode = 'Y'

        assert self.task.get_from_database('Test_y') == 1.0
        aux = self.task.list_accessible_database_entries()
        assert 'Test_x' not in aux
        assert 'Test_amplitude' not in aux
        assert 'Test_phase' not in aux

        self.task.mode = 'X&Y'

        assert self.task.get_from_database('Test_x') == 1.0
        assert self.task.get_from_database('Test_y') == 1.0
        aux = self.task.list_accessible_database_entries()
        assert 'Test_amplitude' not in aux
        assert 'Test_phase' not in aux

        self.task.mode = 'Amp'

        assert self.task.get_from_database('Test_amplitude') == 1.0
        aux = self.task.list_accessible_database_entries()
        assert 'Test_x' not in aux
        assert 'Test_y' not in aux
        assert 'Test_phase' not in aux

        self.task.mode = 'Phase'

        assert self.task.get_from_database('Test_phase') == 1.0
        aux = self.task.list_accessible_database_entries()
        assert 'Test_x' not in aux
        assert 'Test_y' not in aux
        assert 'Test_amplitude' not in aux

        self.task.mode = 'Amp&Phase'

        assert self.task.get_from_database('Test_amplitude') == 1.0
        assert self.task.get_from_database('Test_phase') == 1.0
        aux = self.task.list_accessible_database_entries()
        assert 'Test_x' not in aux
        assert 'Test_y' not in aux

    def test_perform1(self):
        self.task.mode = 'X'

        p = self.root.run_time[PROFILES]['Test1']
        p['settings']['S']['read_x'] = [2.0]
        self.root.prepare()

        self.task.perform()
        assert self.root.get_from_database('Test_x') == 2.0

    def test_perform2(self):
        self.task.mode = 'Y'

        p = self.root.run_time[PROFILES]['Test1']
        p['settings']['S']['read_y'] = [2.0]
        self.root.prepare()

        self.task.perform()
        assert self.root.get_from_database('Test_y') == 2.0

    def test_perform3(self):
        self.task.mode = 'X&Y'

        p = self.root.run_time[PROFILES]['Test1']
        p['settings']['S']['read_xy'] = [(2.0, 3.0)]
        self.root.prepare()

        self.task.perform()
        assert self.root.get_from_database('Test_x') == 2.0
        assert self.root.get_from_database('Test_y') == 3.0

    def test_perform4(self):
        self.task.mode = 'Amp'

        p = self.root.run_time[PROFILES]['Test1']
        p['settings']['S']['read_amplitude'] = [2.0]
        self.root.prepare()

        self.task.perform()
        assert self.root.get_from_database('Test_amplitude') == 2.0

    def test_perform5(self):
        self.task.mode = 'Phase'

        p = self.root.run_time[PROFILES]['Test1']
        p['settings']['S']['read_phase'] = [2.0]
        self.root.prepare()

        self.task.perform()
        assert self.root.get_from_database('Test_phase') == 2.0

    def test_perform6(self):
        self.task.mode = 'Amp&Phase'

        p = self.root.run_time[PROFILES]['Test1']
        p['settings']['S']['read_amp_and_phase'] = [(2.0, 3.0)]
        self.root.prepare()

        self.task.perform()
        assert self.root.get_from_database('Test_amplitude') == 2.0
        assert self.root.get_from_database('Test_phase') == 3.0


@pytest.mark.ui
def test_lock_in_meas_view1(exopy_qtbot, root_view, task_workbench):
    """Test LockInMeasView widget outisde of a LoopTask.

    """
    task = LockInMeasureTask(name='Test')
    root_view.task.add_child_task(0, task)
    show_and_close_widget(exopy_qtbot, LockInMeasView(task=task, root=root_view))
