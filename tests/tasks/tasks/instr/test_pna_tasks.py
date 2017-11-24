# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tests for the PNA tasks

"""
from multiprocessing import Event

import pytest
import enaml

from exopy.tasks.api import RootTask
from exopy.testing.util import show_and_close_widget
from exopy_hqc_legacy.tasks.tasks.instr.rf_tasks\
    import (SetRFFrequencyTask, SetRFPowerTask)
from exopy_hqc_legacy.tasks.tasks.instr.pna_tasks\
    import (PNASetRFFrequencyInterface, PNASetRFPowerInterface,
            PNASinglePointMeasureTask, PNASweepTask)

with enaml.imports():
    from exopy_hqc_legacy.tasks.tasks.instr.views.rf_views\
        import (RFFrequencyView, RFPowerView)
    from exopy_hqc_legacy.tasks.tasks.instr.views.pna_task_views\
        import (PNASinglePointView, PNASweepMeasView)

from .instr_helper import InstrHelper, InstrHelperStarter, PROFILES, DRIVERS


class TestPNASetRFFrequencyTask(object):
    """Test of the PNA set frequency interface.

    """

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

    def test_check_pna_interface1(self):
        """Simply test that everything is ok if frequency can be evaluated.

        """
        self.task.interface = PNASetRFFrequencyInterface(task=self.task,
                                                         channel=1)
        self.task.frequency = '1.0'

        c = self.root.run_time[PROFILES]['Test1']['connections']
        c['C'] = {'defined_channels': [[1]]}

        test, traceback = self.task.check(test_instr=True)
        assert test
        assert not traceback

    def test_check_pna_interface2(self):
        """Check handling a wrong channel.

        """
        self.task.interface = PNASetRFFrequencyInterface(task=self.task,
                                                         channel=1)
        self.task.frequency = '1.0'

        c = self.root.run_time[PROFILES]['Test1']['connections']
        c['C'] = {'defined_channels': [[2]]}

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1

    def test_perform_pna_interface(self):
        """Test setting the frequency through the interface.

        """
        self.task.interface = PNASetRFFrequencyInterface(task=self.task)
        self.task.frequency = '1.0'

        c = self.root.run_time[PROFILES]['Test1']['connections']
        c['C'] = {'frequency': [0.0], 'owner': [None]}
        s = self.root.run_time[PROFILES]['Test1']['settings']
        s['S'] = {'get_channel': lambda x, i: x}

        self.root.prepare()

        self.task.perform()
        assert self.root.get_from_database('Test_frequency') == 1.0e9


@pytest.mark.ui
def test_pna_frequency_view(exopy_qtbot, root_view, task_workbench):
    """Test PNA frequency interface widget outisde of a LoopTask.

    """
    task = SetRFFrequencyTask(name='Test')
    task.interface = PNASetRFFrequencyInterface(task=task)
    root_view.task.add_child_task(0, task)
    show_and_close_widget(exopy_qtbot, RFFrequencyView(task=task, root=root_view))


class TestPNASetRFPowerTask(object):
    """Test of the PNA set power interface.

    """

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

    def test_check_pna_interface1(self):
        """Simply test that everything is ok if power can be evaluated.

        """
        self.task.interface = PNASetRFPowerInterface(task=self.task,
                                                     channel=1)
        self.task.power = '1.0'
        c = self.root.run_time[PROFILES]['Test1']['connections']
        c['C'] = {'defined_channels': [[1]]}

        test, traceback = self.task.check(test_instr=True)
        assert test
        assert not traceback

    def test_check_pna_interface2(self):
        """Check handling a wrong channel.

        """
        self.task.interface = PNASetRFPowerInterface(task=self.task,
                                                     channel=2)
        self.task.power = '1.0'
        c = self.root.run_time[PROFILES]['Test1']['connections']
        c['C'] = {'defined_channels': [[1]]}

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1

    def test_perform_pna_interface(self):
        self.task.interface = PNASetRFPowerInterface(task=self.task,
                                                     channel=1)
        self.task.power = '1.0'

        c = self.root.run_time[PROFILES]['Test1']['connections']
        c['C'] = {'power': [0.0], 'port': [1], 'owner': [None]}
        s = self.root.run_time[PROFILES]['Test1']['settings']
        s['S'] = {'get_channel': lambda x, i: x}

        self.root.prepare()

        self.task.perform()
        assert self.root.get_from_database('Test_power') == 1.0


@pytest.mark.ui
def test_pna_power_view(exopy_qtbot, root_view, task_workbench):
    """Test PNA power interface widget outisde of a LoopTask.

    """
    task = SetRFPowerTask(name='Test')
    task.interface = PNASetRFPowerInterface(task=task)
    root_view.task.add_child_task(0, task)
    show_and_close_widget(exopy_qtbot, RFPowerView(task=task, root=root_view))


class TestPNASinglePointMeasureTask(object):
    """Test PNASinglePointMeasureTask.

    """
    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = PNASinglePointMeasureTask(name='Test')
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

    def test_measure_observation(self):
        pass

    def test_check1(self):
        """Simply test that everything is ok.

        """
        self.task.measures = [('S21', ''), ('S33', 'MLIN')]

        c = self.root.run_time[PROFILES]['Test1']['connections']
        c['C'] = {'defined_channels': [[1]]}

        test, traceback = self.task.check(test_instr=True)
        assert test
        assert not traceback

    def test_check2(self):
        """Check handling a wrong channel.

        """
        self.task.measures = [('S21', ''), ('S33', 'MLIN')]

        c = self.root.run_time[PROFILES]['Test1']['connections']
        c['C'] = {'defined_channels': [[3]]}

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1

    def test_check3(self):
        """Check handling a wrong S parameter.

        """
        self.task.measures = [('S21', ''), ('SF3', 'MLIN')]

        c = self.root.run_time[PROFILES]['Test1']['connections']
        c['C'] = {'defined_channels': [[1]]}

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1

#    def test_perform(self):
#        self.task.measures = [('S21', ''), ('S33', 'MLIN')]
#
#        profile = {'Test1': ({'defined_channels': [[1]]},
#                             {})}
#        self.root.run_time['profiles'] = profile
#
#        self.root.task_database.prepare_for_running()
#
#        self.task.perform()
#        assert_equal(self.root.get_from_database('Test_output'), 1.0)


@pytest.mark.ui
def test_pna_single_point_view(exopy_qtbot, root_view, task_workbench):
    """Test PNA single point meas view no measure.

    """
    task = PNASinglePointMeasureTask(name='Test')
    root_view.task.add_child_task(0, task)
    show_and_close_widget(exopy_qtbot, PNASinglePointView(task=task, root=root_view))


@pytest.mark.ui
def test_pna_single_point_view2(exopy_qtbot, root_view, task_workbench):
    """Test PNA single point meas view.

    """
    task = PNASinglePointMeasureTask(name='Test')
    task.measures = [('S21', ''), ('S43', 'MLIN')]
    root_view.task.add_child_task(0, task)
    show_and_close_widget(exopy_qtbot, PNASinglePointView(task=task, root=root_view))


#class TestPNASweepTask(object):
#
#    def setup(self):
#        self.root = RootTask(should_stop=Event(), should_pause=Event())
#        self.task = PNASweepTask(name='Test')
#        self.root.children_task.append(self.task)
#        self.root.run_time['drivers'] = {'Test': InstrHelper}
#
#        # This is set simply to make sure the test of InstrTask pass.
#        self.task.selected_driver = 'Test'
#        self.task.selected_profile = 'Test1'
#
#    def test_check1(self):
#        # Simply test that everything is ok if voltage can be evaluated.
#        self.task.switch = '1.0'
#
#        test, traceback = self.task.check(test_instr=True)
#        assert test
#        assert not traceback
#
#    def test_check2(self):
#        # Check handling a wrong voltage.
#        self.task.switch = '*1.0*'
#
#        test, traceback = self.task.check(test_instr=True)
#        assert not test
#        assert len(traceback) == 1
#
#    def test_perform(self):
#        self.task.switch = '1.0'
#
#        self.root.run_time['profiles'] = {'Test1': ({'output': [0.0],
#                                                     'owner': [None]}, {})}
#
#        self.root.task_database.prepare_for_running()
#
#        self.task.perform()
#        assert_equal(self.root.get_from_database('Test_output'), 1.0)
#
#
#@attr('ui')
#class TestPNASweepView(object):
#
#    def setup(self):
#        self.workbench = Workbench()
#        self.workbench.register(CoreManifest())
#        self.workbench.register(StateManifest())
#        self.workbench.register(PreferencesManifest())
#        self.workbench.register(InstrManagerManifest())
#        self.workbench.register(TaskManagerManifest())
#
#        self.root = RootTask(should_stop=Event(), should_pause=Event())
#        self.task = PNASweepTask(name='Test')
#        self.root.children_task.append(self.task)
#        self.root.run_time['drivers'] = {'Test': InstrHelper}
#
#    def teardown(self):
#        close_all_windows()
#
#        self.workbench.unregister(u'hqc_meas.task_manager')
#        self.workbench.unregister(u'hqc_meas.instr_manager')
#        self.workbench.unregister(u'hqc_meas.preferences')
#        self.workbench.unregister(u'hqc_meas.state')
#        self.workbench.unregister(u'enaml.workbench.core')
#
#    def test_view1(self):
#        # Intantiate a view with no selected interface and select one after
#        window = enaml.widgets.api.Window()
#        core = self.workbench.get_plugin('enaml.workbench.core')
#        view = PNASweepMeasView(window, task=self.task, core=core)
#        window.show()
#
#        process_app_events()
#
#        assert_in('AgilentE8257D', view.drivers)
#        self.task.selected_driver = 'AgilentE8257D'
#        process_app_events()
#
#    def test_view2(self):
#        # Intantiate a view with a selected interface.
#        self.task.switch = '1.0'
#        self.task.selected_driver = 'AgilentE8257D'
#
#        interface = self.task.interface
#
#        window = enaml.widgets.api.Window()
#        core = self.workbench.get_plugin('enaml.workbench.core')
#        PNASweepMeasView(window, task=self.task, core=core)
#        window.show()
#
#        process_app_events()
#
#        assert_is(self.task.interface, interface)
