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
from exopy_hqc_legacy.tasks.tasks.instr.meas_dc_tasks\
    import MeasDCVoltageTask

with enaml.imports():
    from exopy_hqc_legacy.tasks.tasks.instr.views.meas_dc_views\
        import MeasDCVoltView

from .instr_helper import InstrHelper, InstrHelperStarter, PROFILES, DRIVERS


class TestSetDCVoltageTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = MeasDCVoltageTask(name='Test')
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

    def test_perform(self):
        self.task.wait_time = 1.0

        p = self.root.run_time[PROFILES]['Test1']
        p['settings']['S']['read_voltage_dc'] = [2.0]
        self.root.prepare()

        self.task.perform()
        assert self.root.get_from_database('Test_voltage') == 2.0


@pytest.mark.ui
def test_meas_dc_voltage_view(exopy_qtbot, root_view, task_workbench):
    """Test MeasDCVoltView widget outisde of a LoopTask.

    """
    task = MeasDCVoltageTask(name='Test')
    root_view.task.add_child_task(0, task)
    show_and_close_widget(exopy_qtbot, MeasDCVoltView(task=task, root=root_view))
