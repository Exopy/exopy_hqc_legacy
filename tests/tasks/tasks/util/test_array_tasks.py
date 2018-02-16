# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the tasks operating on numpy.arrays.

"""
from multiprocessing import Event

import pytest
import enaml
import numpy as np
from exopy.tasks.api import RootTask
from exopy.testing.util import show_and_close_widget

from exopy_hqc_legacy.tasks.tasks.util.array_tasks import (ArrayExtremaTask,
                                                          ArrayFindValueTask)

with enaml.imports():
    from exopy_hqc_legacy.tasks.tasks.util.views.array_views\
        import ArrayExtremaView, ArrayFindValueView


class TestArrayExtremaTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = ArrayExtremaTask(name='Test')
        self.root.add_child_task(0, self.task)
        array = np.zeros((5,), dtype={'names': ['var1', 'var2'],
                                      'formats': ['f8', 'f8']})
        array['var1'][1] = -1
        array['var1'][3] = 1
        self.root.write_in_database('array', array)

    def test_mode_observation(self):
        """Check that the database is correctly updated when the mode change.

        """
        self.task.mode = 'Min'

        assert self.task.get_from_database('Test_min_ind') == 0
        assert self.task.get_from_database('Test_min_value') == 1.0
        aux = self.task.list_accessible_database_entries()
        assert 'Test_max_ind' not in aux
        assert 'Test_max_value' not in aux

        self.task.mode = 'Max'

        assert self.task.get_from_database('Test_max_ind') == 0
        assert self.task.get_from_database('Test_max_value') == 2.0
        aux = self.task.list_accessible_database_entries()
        assert 'Test_min_ind' not in aux
        assert 'Test_min_value' not in aux

        self.task.mode = 'Max & min'

        assert self.task.get_from_database('Test_min_ind') == 0
        assert self.task.get_from_database('Test_min_value') == 1.0
        assert self.task.get_from_database('Test_max_ind') == 0
        assert self.task.get_from_database('Test_max_value') == 2.0

    def test_check1(self):
        """Simply test that everything is ok if the array exists in the
        database.

        """
        self.root.write_in_database('array', np.zeros((5,)))
        self.task.target_array = '{array}'

        test, traceback = self.task.check()
        assert test
        assert not traceback

    def test_check2(self):
        """Simply test that everything is ok if the array exists in the
        database and the column name is ok.

        """
        self.task.target_array = '{array}'
        self.task.column_name = 'var1'

        test, traceback = self.task.check()
        assert test
        assert not traceback

    def test_check3(self):
        """Test handling a wrong array name.

        """
        self.task.target_array = '*{array}'
        self.task.column_name = 'var3'

        test, traceback = self.task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Test-target_array' in traceback

    def test_check4(self):
        """Test handling an array without names when a name is given.

        """
        self.root.write_in_database('array', np.zeros((5,)))
        self.task.target_array = '{array}'
        self.task.column_name = 'var1'

        test, traceback = self.task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Test' in traceback

    def test_check5(self):
        """Test handling an array with names when no name is given.

        """
        self.task.target_array = '{array}'

        test, traceback = self.task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Test' in traceback

    def test_check6(self):
        """Test handling a wrong column name.

        """
        self.task.target_array = '{array}'
        self.task.column_name = 'var3'

        test, traceback = self.task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Test' in traceback

    def test_check7(self):
        """Test handling a 2d array without names.

        """
        self.task.target_array = '{array}'

        array = np.zeros((5, 5))
        self.root.write_in_database('array', array)

        test, traceback = self.task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Test' in traceback

    def test_perform1(self):
        """Test performing when mode is 'Max'.

        """
        self.task.mode = 'Max'
        self.task.target_array = '{array}'
        self.task.column_name = 'var1'
        self.root.prepare()

        self.task.perform()

        assert self.task.get_from_database('Test_max_ind') == 3
        assert self.task.get_from_database('Test_max_value') == 1.0

    def test_perform2(self):
        """Test performing when mode is 'Min'.

        """
        self.task.mode = 'Min'
        self.task.target_array = '{array}'
        self.task.column_name = 'var1'
        self.root.prepare()

        self.task.perform()

        assert self.task.get_from_database('Test_min_ind') == 1
        assert self.task.get_from_database('Test_min_value') == -1.0

    def test_perform3(self):
        """Test performing when mode is 'Max & min'.

        """
        self.task.mode = 'Max & min'
        self.task.target_array = '{array}'
        self.task.column_name = 'var1'
        self.root.prepare()

        self.task.perform()

        assert self.task.get_from_database('Test_max_ind') == 3
        assert self.task.get_from_database('Test_max_value') == 1.0
        assert self.task.get_from_database('Test_min_ind') == 1
        assert self.task.get_from_database('Test_min_value') == -1.0

    def test_perform4(self):
        """Test performing when no column name is given.

        """
        self.root.write_in_database('array', np.zeros((5,)))
        self.task.mode = 'Max'
        self.task.target_array = '{array}'
        self.root.prepare()

        self.task.perform()

        assert self.task.get_from_database('Test_max_ind') == 0
        assert self.task.get_from_database('Test_max_value') == 0.0


@pytest.mark.ui
def test_array_extrema_view(exopy_qtbot):
    """Test the array extrema view.

    """
    root = RootTask(should_stop=Event(), should_pause=Event())
    task = ArrayExtremaTask(name='Test')
    root.children.append(task)

    show_and_close_widget(exopy_qtbot, ArrayExtremaView(task=task))


class TestArrayFindValueTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = ArrayFindValueTask(name='Test')
        self.root.add_child_task(0, self.task)
        array = np.zeros((5,), dtype={'names': ['var1', 'var2'],
                                      'formats': ['f8', 'f8']})
        array['var1'][1] = -1.5
        array['var1'][3] = 1.6359
        array['var1'][4] = 1.6359
        self.root.write_in_database('array', array)

    def test_check1(self):
        """Simply test that everything is ok if the array exists in the
        database and value can be evaluated.

        """
        self.root.write_in_database('array', np.zeros((5,)))
        self.task.target_array = '{array}'
        self.task.value = '1.6359'

        test, traceback = self.task.check()
        assert test
        assert not traceback

    def test_check2(self):
        """Simply test that everything is ok if the array exists in the
        database the column name is ok, and value can be evaluated.

        """
        self.task.target_array = '{array}'
        self.task.column_name = 'var1'
        self.task.value = '1.6359'

        test, traceback = self.task.check()
        assert test
        assert not traceback

    def test_check3(self):
        """Test handling a wrong array name.

        """
        self.task.target_array = '*{array}'
        self.task.column_name = 'var3'
        self.task.value = '1.6359'

        test, traceback = self.task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Test-target_array' in traceback

    def test_check4(self):
        """Test handling an array without names when a name is given.

        """
        self.root.write_in_database('array', np.zeros((5,)))
        self.task.target_array = '{array}'
        self.task.column_name = 'var1'
        self.task.value = '1.6359'

        test, traceback = self.task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Test' in traceback

    def test_check5(self):
        """Test handling an array with names when no name is given.

        """
        self.task.target_array = '{array}'
        self.task.value = '1.6359'

        test, traceback = self.task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Test' in traceback

    def test_check6(self):
        """Test handling a wrong column name.

        """
        self.task.target_array = '{array}'
        self.task.column_name = 'var3'
        self.task.value = '1.6359'

        test, traceback = self.task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Test' in traceback

    def test_check7(self):
        """Test handling a wrong value.

        """
        self.task.target_array = '{array}'
        self.task.column_name = 'var1'
        self.task.value = '*1.6359'

        test, traceback = self.task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Test-value' in traceback

    def test_check8(self):
        """Test handling a 2d array value.

        """
        self.task.target_array = '{array}'
        self.task.value = '1.6359'

        array = np.zeros((5, 5))
        self.root.write_in_database('array', array)

        test, traceback = self.task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Test' in traceback

    def test_perform1(self):
        """Test performing.

        """
        self.task.value = '1.6359'
        self.task.target_array = '{array}'
        self.task.column_name = 'var1'
        self.root.prepare()

        self.task.perform()

        assert self.task.get_from_database('Test_index') == 3


@pytest.mark.ui
def test_array_find_value_view(exopy_qtbot):
    """Test the array extrema view.

    """
    root = RootTask(should_stop=Event(), should_pause=Event())
    task = ArrayFindValueTask(name='Test')
    root.children.append(task)

    show_and_close_widget(exopy_qtbot, ArrayFindValueView(task=task))
