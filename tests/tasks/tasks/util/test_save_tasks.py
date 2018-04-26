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
from collections import OrderedDict

import pytest
import enaml
import numpy as np

from exopy.tasks.api import RootTask
from exopy.testing.util import (show_and_close_widget, show_widget)
from exopy_hqc_legacy.tasks.tasks.util.save_tasks import (SaveTask,
                                                          SaveArrayTask,
                                                          SaveFileTask)

with enaml.imports():
    from exopy_hqc_legacy.tasks.tasks.util.views.save_views\
        import (SaveView, SaveArrayView, SaveFileView)

pytest_plugins = str('exopy.testing.tasks.fixtures'),


class TestSaveTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SaveTask(name='Test')
        self.root.add_child_task(0, self.task)

        self.root.write_in_database('int', 1)
        self.root.write_in_database('float', 2.0)
        self.root.write_in_database('str', 'a')

    def test_saving_target_observer(self):
        """Test that changing the target does change the database content.

        """
        self.task.saving_target = 'Array'

        assert self.task.get_from_database('Test_array') == np.array([1.0])

        self.task.saving_target = 'File'

        aux = self.task.list_accessible_database_entries()
        assert 'Test_array' not in aux

        self.task.saving_target = 'File and array'

        assert self.task.get_from_database('Test_array') == np.array([1.0])

    def test_check1(self, tmpdir):
        """Test everything ok in file mode (no array size).

        """
        task = self.task
        task.saving_target = 'File'
        task.folder = str(tmpdir)
        task.filename = 'test{int}.txt'
        task.file_mode = 'New'
        task.header = 'test'
        task.saved_values = OrderedDict([('toto', '{str}'),
                                         ('tata', '{float}')])
        file_path = os.path.join(str(tmpdir), 'test1.txt')

        test, traceback = task.check()
        assert test and not traceback
        assert not os.path.isfile(file_path)
        assert not task.initialized

        task.file_mode = 'Add'

        test, traceback = task.check()
        assert test and not traceback
        assert os.path.isfile(file_path)

    def test_check2(self):
        """Test everything ok in array mode (assert database state).

        """
        task = self.task
        task.saving_target = 'Array'
        task.array_size = '1000*{float}'
        task.saved_values = OrderedDict([('toto', '{str}'),
                                         ('tata', '{float}')])

        test, traceback = task.check()
        assert test and not traceback
        array = task.get_from_database('Test_array')
        assert array.dtype.names == ('toto', 'tata')

    def test_check3(self, tmpdir):
        """Test everything is ok in file & array mode.

        """
        task = self.task
        task.saving_target = 'File and array'
        task.folder = str(tmpdir)
        task.filename = 'test_rr.txt'
        task.file_mode = 'New'
        task.header = 'test'
        task.array_size = '1000*{float}'
        task.saved_values = OrderedDict([('toto', '{str}'),
                                         ('tata', '{float}')])
        file_path = os.path.join(str(tmpdir), 'test_rr.txt')

        test, traceback = task.check()
        assert test and not traceback
        assert not os.path.isfile(file_path)
        array = task.get_from_database('Test_array')
        assert array.dtype.names == ('toto', 'tata')

    def test_check4(self, tmpdir):
        """Test check issues in file mode : folder.

        """
        task = self.task
        task.saving_target = 'File'
        task.folder = str(tmpdir) + '{tt}'

        test, traceback = task.check()
        assert not test
        assert len(traceback) == 1

    def test_check5(self, tmpdir):
        """Test check issues in file mode : file.

        """
        task = self.task
        task.saving_target = 'File'
        task.folder = str(tmpdir)
        task.filename = 'test{tt}.txt'

        test, traceback = task.check()
        assert not test
        assert len(traceback) == 1

    def test_check6(self, tmpdir):
        """Test check issues in file mode : array_size.

        """
        task = self.task
        task.saving_target = 'File'
        task.folder = str(tmpdir)
        task.filename = 'test.txt'
        task.file_mode = 'New'
        task.header = 'test'
        task.array_size = '1000*'
        task.saved_values = OrderedDict([('toto', '{str}'),
                                         ('tata', '{float}')])
        file_path = os.path.join(str(tmpdir), 'test.txt')

        test, traceback = task.check()
        assert not test
        assert len(traceback) == 1
        assert not os.path.isfile(file_path)

    def test_check6bis(self, tmpdir):
        """Test check issues in file mode : header formatting.

        """
        task = self.task
        task.saving_target = 'File'
        task.folder = str(tmpdir)
        task.filename = 'test.txt'
        task.file_mode = 'New'
        task.header = 'test {*}'
        task.array_size = '1000'
        task.saved_values = OrderedDict([('toto', '{str}'),
                                         ('tata', '{float}')])
        file_path = os.path.join(str(tmpdir), 'test.txt')

        test, traceback = task.check()
        assert not test
        assert len(traceback) == 1
        assert not os.path.isfile(file_path)

    def test_check7(self):
        """Test check issues in array mode  : wrong array_size.

        """
        task = self.task
        task.saving_target = 'Array'
        task.array_size = '1000*{float}*'
        task.saved_values = OrderedDict([('toto', '{str}'),
                                         ('tata', '{float}')])

        test, traceback = task.check()
        assert not test
        assert len(traceback) == 1
        assert self.task.get_from_database('Test_array') == np.array([1.0])

    def test_check8(self):
        """Test check issues in array mode : absent array_size.

        """
        task = self.task
        task.saving_target = 'Array'
        task.saved_values = OrderedDict([('toto', '{str}'),
                                         ('tata', '{float}')])

        test, traceback = task.check()
        assert not test
        assert len(traceback) == 1
        assert self.task.get_from_database('Test_array') == np.array([1.0])

    def test_check9(self):
        """Test check issues in entrie.

        """
        task = self.task
        task.saving_target = 'Array'
        task.array_size = '1000*{float}'
        task.saved_values = OrderedDict([('toto', '*{str}'),
                                         ('tat{str}', '{float}@')])

        test, traceback = task.check()
        assert not test
        assert len(traceback) == 2

    def test_check9bis(self):
        """Test check issues in label.

        """
        task = self.task
        task.saving_target = 'Array'
        task.array_size = '1000*{float}'
        task.saved_values = OrderedDict([('toto', '{str}'),
                                         ('tat{str*}', '{float}')])

        test, traceback = task.check()
        assert not test
        assert len(traceback) == 1

    def test_check10(self, tmpdir):
        """Test warning in case the file already exists in new mode.

        """
        task = self.task
        task.saving_target = 'File'
        task.folder = str(tmpdir)
        task.filename = 'test_e.txt'
        task.file_mode = 'New'
        task.header = 'test'
        task.saved_values = OrderedDict([('toto', '{str}'),
                                         ('tat{str}', '{float}')])

        file_path = os.path.join(str(tmpdir), 'test_e.txt')
        with open(file_path, 'w'):
            pass

        assert os.path.isfile(file_path)
        test, traceback = task.check()
        assert test and traceback
        assert os.path.isfile(file_path)

    def test_perform1(self, tmpdir):
        """Test performing in mode file. (Call three times perform)

        """
        task = self.task
        task.saving_target = 'File'
        task.folder = str(tmpdir)
        task.filename = 'test_perform{int}.txt'
        task.file_mode = 'Add'
        task.header = 'test {str}'
        task.array_size = '3'
        task.saved_values = OrderedDict([('toto', '{str}'),
                                         ('tat{str}', '{float}')])

        file_path = os.path.join(str(tmpdir), 'test_perform1.txt')

        with open(file_path, 'w') as f:
            f.write('test\n')

        task.perform()

        assert task.initialized
        assert task.file_object
        assert task.line_index == 1
        with open(file_path) as f:
            a = f.readlines()
            assert a == ['test\n', '# test a\n', 'toto\ttata\n', 'a\t2.0\n']

        task.perform()

        assert task.initialized
        assert task.line_index == 2
        with open(file_path) as f:
            a = f.readlines()
            assert (a == ['test\n', '# test a\n', 'toto\ttata\n', 'a\t2.0\n',
                          'a\t2.0\n'])

        task.perform()

        assert not task.initialized
        assert task.line_index == 3
        with open(file_path) as f:
            a = f.readlines()
            assert a == ['test\n', '# test a\n', 'toto\ttata\n',
                         'a\t2.0\n', 'a\t2.0\n', 'a\t2.0\n']

    def test_perform2(self):
        """Test performing in array mode. (Call three times perform)

        """
        task = self.task
        task.saving_target = 'Array'
        task.array_size = '3'
        task.saved_values = OrderedDict([('toto', '{int}'),
                                         ('tat{str}', '{float}')])

        task.perform()

        assert task.initialized
        assert task.line_index == 1

        task.perform()

        assert task.initialized
        assert task.line_index == 2

        task.perform()

        assert not task.initialized
        assert task.line_index == 3

        dtype = np.dtype({'names': [task.format_string(s)
                                    for s in task.saved_values],
                          'formats': ['f8']*len(task.saved_values)})
        array = np.empty((3),  dtype)
        array[0] = (1, 2.0)
        array[1] = (1, 2.0)
        array[2] = (1, 2.0)
        np.testing.assert_array_equal(task.array, array)


class TestSaveFileTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SaveFileTask(name='Test')
        self.root.add_child_task(0, self.task)

        self.root.write_in_database('int', 1)
        self.root.write_in_database('float', 2.0)
        self.root.write_in_database('array', np.array(range(10)))

    def test_check1(self, tmpdir):
        """Test everything ok in file mode (no array size).

        """
        task = self.task
        task.folder = str(tmpdir)
        task.filename = 'test{int}.txt'
        task.saved_values = OrderedDict([('toto', '{int}'),
                                         ('tata', '{float}')])
        file_path = os.path.join(str(tmpdir), 'test1.txt')

        test, traceback = task.check()
        assert test
        assert not os.path.isfile(file_path)
        assert not task.initialized

    def test_check4(self, tmpdir):
        """Test check issues in file mode : folder.

        """
        task = self.task
        task.folder = str(tmpdir) + '{tt}'

        test, traceback = task.check()
        assert not test
        assert len(traceback) == 1

    def test_check5(self, tmpdir):
        """Test check issues in file mode : file.

        """
        task = self.task
        task.folder = str(tmpdir)
        task.filename = 'test{tt}.txt'

        test, traceback = task.check()
        assert not test
        assert len(traceback) == 1

    def test_check6(self, tmpdir):
        """Test check issues in file mode : header formatting.

        """
        task = self.task
        task.folder = str(tmpdir)
        task.filename = 'test.txt'
        task.header = 'test {*}'

        test, traceback = task.check()
        assert not test
        assert len(traceback) == 1

    def test_check9(self, tmpdir):
        """Test check issues in entries.

        """
        task = self.task
        task.folder = str(tmpdir)
        self.root.write_in_database('int', 3)
        task.filename = 'test{int}.txt'
        task.saved_values = OrderedDict([('toto', '{int*}'),
                                         ('tata', '{float*}')])

        test, traceback = task.check()
        assert not test
        assert len(traceback) == 2

    def test_check10(self, tmpdir):
        """Test warning in case the file already exists in new mode.

        """
        task = self.task
        task.folder = str(tmpdir)
        task.filename = 'test_e.txt'
        task.header = 'test'
        task.saved_values = OrderedDict([('toto', '{int}'),
                                         ('tata', '{float}')])
        file_path = os.path.join(str(tmpdir), 'test_e.txt')
        with open(file_path, 'w'):
            pass

        assert os.path.isfile(file_path)
        test, traceback = task.check()
        assert test
        assert traceback
        assert os.path.isfile(file_path)

    def test_perform1(self, tmpdir):
        """Test performing with non rec array. (Call twice perform)

        """
        task = self.task
        task.folder = str(tmpdir)
        task.filename = 'test_perform{int}.txt'
        task.header = 'test {float}'
        task.saved_values = OrderedDict([('toto', '{float}'),
                                         ('tata', '{array}')])
        file_path = os.path.join(str(tmpdir), 'test_perform1.txt')

        with open(file_path, 'w') as f:
            f.write('test\n')

        try:
            task.perform()

            assert task.initialized
            assert task.file_object
            with open(file_path) as f:
                a = f.readlines()

            assert a[:2] == ['# test 2.0\n', 'toto\ttata\n']
            for i in range(10):
                assert float(a[2+i].split('\t')[0]) == 2.0
                assert float(a[2+i].split('\t')[1]) == float(i)

            task.perform()

            assert task.initialized
            with open(file_path) as f:
                a = f.readlines()
            assert float(a[12].split('\t')[0]) == 2.0
            assert float(a[12].split('\t')[1]) == 0.0

            task.perform()
        finally:
            task.file_object.close()

    def test_perform2(self, tmpdir):
        """Test performing with a rec array. (Call twice perform)

        """
        self.root.write_in_database('array',
                                    np.rec.fromarrays([range(10), range(10)],
                                                      names=['a', 'b']))
        task = self.task
        task.folder = str(tmpdir)
        task.filename = 'test_perform_rec.txt'
        task.header = 'test'
        task.saved_values = OrderedDict([('toto', '{float}'),
                                         ('tata', '{array}')])
        file_path = os.path.join(str(tmpdir), 'test_perform_rec.txt')

        with open(file_path, 'w') as f:
            f.write('test\n')

        try:
            task.perform()

            assert task.initialized
            assert task.file_object
            with open(file_path) as f:
                a = f.readlines()

            assert a[:2] == ['# test\n', 'toto\ttata_a\ttata_b\n']

            for i in range(10):
                assert float(a[2+i].split('\t')[0]) == 2.0
                assert float(a[2+i].split('\t')[1]) == float(i)

            task.perform()

            assert task.initialized
            with open(file_path) as f:
                a = f.readlines()

            assert float(a[12].split('\t')[0]) == 2.0
            assert float(a[12].split('\t')[1]) == 0.0

            task.perform()
        finally:
            task.file_object.close()


class TestSaveArrayTask(object):

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SaveArrayTask(name='Test')
        self.root.add_child_task(0, self.task)

        array = np.empty(2, dtype={'names': ('a', 'b'),
                                   'formats': ('f8', 'f8')})
        array[0] = (0, 1)
        array[1] = (2, 3)
        self.root.write_in_database('array', array)
        self.root.write_in_database('float', 2.0)
        self.root.write_in_database('str', 'a')

    def test_check1(self, tmpdir):
        """Check everything ok in Text mode.

        """
        array = np.empty(2, dtype={'names': ('a', 'b'),
                                   'formats': ('f8', 'f8')})
        self.root.write_in_database('arrays', {'a': array})
        task = self.task
        task.folder = str(tmpdir)
        task.filename = 'test_perform{str}.txt'
        task.mode = 'Text file'
        task.header = 'teststs'
        task.target_array = '{arrays}["a"]'

        test, traceback = task.check()

        assert test
        assert not os.path.isfile(os.path.join(str(tmpdir),
                                               'test_performa.txt'))

    def test_check2(self, tmpdir):
        """Check everything ok in Binary mode (wrong file extension, and
        header)

        """
        task = self.task
        task.folder = str(tmpdir)
        task.filename = 'test_perform{str}.txt'
        task.mode = 'Binary file'
        task.header = 'teststs'
        task.target_array = '{array}'

        test, traceback = task.check()

        assert test
        assert len(traceback) == 2
        assert 'root/Test-header' in traceback
        assert 'root/Test-file_ext' in traceback
        assert not os.path.isfile(os.path.join(str(tmpdir),
                                               'test_performa.npy'))

    def test_check3(self, tmpdir):
        """Check handling a wrong folder.

        """
        task = self.task
        task.folder = str(tmpdir) + '{eee}'
        task.target_array = '{array}'

        test, traceback = task.check()

        assert not test
        assert len(traceback) == 1

    def test_check4(self, tmpdir):
        """Check handling a wrong filename.

        """
        task = self.task
        task.folder = str(tmpdir)
        task.filename = '{rr}'
        task.target_array = '{array}'

        test, traceback = task.check()

        assert not test
        assert len(traceback) == 1

    def test_check5(self, tmpdir):
        """Check handling a wrong database address.

        """
        task = self.task
        task.folder = str(tmpdir)
        task.filename = 'test_perform{str}.txt'
        task.mode = 'Text file'
        task.header = 'teststs'
        task.target_array = '**{array}'

        test, traceback = task.check()

        assert not test
        assert len(traceback) == 1

    def test_check6(self, tmpdir):
        """Check handling a wrong type.

        """
        self.root.write_in_database('array', 1.0)
        task = self.task
        task.folder = str(tmpdir)
        task.filename = 'test_perform{str}.txt'
        task.mode = 'Text file'
        task.header = 'teststs'
        task.target_array = '{array}'

        test, traceback = task.check()

        assert not test
        assert len(traceback) == 1

    def test_perform1(self, tmpdir):
        """Test performing in text mode.

        """
        task = self.task
        task.folder = str(tmpdir)
        task.filename = 'test_perform{str}.txt'
        task.mode = 'Text file'
        task.header = 'tests'
        task.target_array = '{array}'

        task.perform()

        path = os.path.join(str(tmpdir), 'test_performa.txt')
        assert os.path.isfile(path)
        with open(path) as f:
            lines = f.readlines()
            assert lines[0:2] == ['# tests\n', 'a\tb\n']
            assert [float(x) for x in lines[2][:-1].split('\t')] == [0.0, 1.0]
            assert [float(x) for x in lines[3][:-1].split('\t')] == [2.0, 3.0]

    def test_perform1bis(self, tmpdir):
        # Test performing in text mode wrong type.
        self.root.write_in_database('array', 1.0)
        task = self.task
        task.folder = str(tmpdir)
        task.filename = 'test_perform{str}.txt'
        task.mode = 'Text file'
        task.header = 'tests'
        task.target_array = '{array}'

        with pytest.raises(AssertionError):
            task.perform()

    def test_perform2(self, tmpdir):
        """Test performing in binary mode.

        """
        task = self.task
        task.folder = str(tmpdir)
        task.filename = 'test_perform{str}.npy'
        task.mode = 'Binary file'
        task.target_array = '{array}'

        task.perform()

        path = os.path.join(str(tmpdir), 'test_performa.npy')
        assert os.path.isfile(path)
        # TODO understand weird numpy bug
#        a = np.load(path)
#        np.testing.assert_array_equal(a, task.get_from_database('array'))


@pytest.mark.ui
def test_save_view(exopy_qtbot, dialog_sleep, root_view):
    """Test SaveView widget.

    """
    task = SaveTask(name='Test')
    root_view.task.add_child_task(0, task)
    view = SaveView(task=task, root=root_view)
    win = show_widget(exopy_qtbot, view)
    exopy_qtbot.wait(dialog_sleep)

    d_editor = view.widgets()[-1]
    d_editor._model.add_pair(0)
    exopy_qtbot.wait(dialog_sleep)

    win.close()


@pytest.mark.ui
def test_save_file_view(exopy_qtbot, root_view):
    """Test SaveView widget.

    """
    task = SaveFileTask(name='Test')
    root_view.task.add_child_task(0, task)
    show_and_close_widget(exopy_qtbot, SaveFileView(task=task, root=root_view))


@pytest.mark.ui
def test_save_array_view(exopy_qtbot, root_view):
    """Test SaveView widget.

    """
    task = SaveArrayTask(name='Test')
    root_view.task.add_child_task(0, task)
    show_and_close_widget(exopy_qtbot,
                          SaveArrayView(task=task, root=root_view))
