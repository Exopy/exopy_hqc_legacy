# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the taskused to load files.

"""
import os
from multiprocessing import Event

import pytest
import enaml
import numpy as np

from exopy.tasks.api import RootTask
from exopy.testing.util import show_widget
from exopy_hqc_legacy.tasks.tasks.util.load_tasks import (LoadArrayTask,
                                                         CSVLoadInterface)

with enaml.imports():
    from exopy_hqc_legacy.tasks.tasks.util.views.load_views import LoadArrayView


@pytest.fixture
def fake_data(tmpdir):
    """Create some false data for testing.

    """
    data = np.zeros((5,), dtype={'names': ['Freq', 'Log'],
                                 'formats': ['f8', 'f8']})
    full_path = os.path.join(str(tmpdir), 'fake.dat')
    with open(full_path, 'wb') as f:

        f.write('# this is a comment \n'.encode('utf-8'))
        f.write(('\t'.join(data.dtype.names) + '\n').encode('utf-8'))

        np.savetxt(f, data, delimiter='\t')

    return data


@pytest.fixture
def load_array_task(tmpdir, fake_data):
    """Build a LoadArrayTask for testing purposes.

    """
    root = RootTask(should_stop=Event(), should_pause=Event())
    task = LoadArrayTask(name='Test')
    task.interface = CSVLoadInterface()
    task.folder = str(tmpdir)
    task.filename = 'fake.dat'
    root.add_child_task(0, task)
    return task


def test_check1(load_array_task):
    """Test everything is ok if folder and filename are correct.

    """
    test, traceback = load_array_task.check()
    assert test
    assert not traceback
    array = load_array_task.get_from_database('Test_array')
    assert array.dtype.names == ('Freq', 'Log')


def test_check2(load_array_task):
    """Test handling wrong folder and filename.

    """
    load_array_task.folder = '{rr}'
    load_array_task.filename = '{tt}'
    test, traceback = load_array_task.check()
    assert not test
    assert len(traceback) == 2


def test_check3(load_array_task):
    """Test handling an absent file.

    """
    load_array_task.filename = 'tt'
    test, traceback = load_array_task.check()
    assert test
    assert len(traceback) == 1


def test_perform1(load_array_task, fake_data):
    """Test loading a csv file.

    """
    load_array_task.perform()
    array = load_array_task.get_from_database('Test_array')
    np.testing.assert_array_equal(array, fake_data)


@pytest.mark.ui
class TestLoadArrayView(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = LoadArrayTask(name='Test')
        self.root.add_child_task(0, self.task)

    def test_view(self, exopy_qtbot, root_view, task_workbench,
                  dialog_sleep):
        """Intantiate a view with no selected interface and select one after

        """
        view = LoadArrayView(task=self.task, root=root_view)
        win = show_widget(exopy_qtbot, view)
        exopy_qtbot.wait(dialog_sleep)

        assert self.task.interface is None

        assert 'CSV' in view.file_formats
        self.task.selected_format = 'CSV'
        exopy_qtbot.wait(dialog_sleep)
        assert isinstance(self.task.interface, CSVLoadInterface)

        win.close()

    def test_view2(self, exopy_qtbot, root_view, task_workbench,
                   dialog_sleep):
        """Intantiate a view with a selected interface.

        """
        interface = CSVLoadInterface()
        self.task.interface = interface
        self.task.selected_format = 'CSV'

        interface = self.task.interface

        view = LoadArrayView(task=self.task, root=root_view)
        win = show_widget(exopy_qtbot, view)

        exopy_qtbot.wait(dialog_sleep)

        assert self.task.interface is interface
        win.close()
