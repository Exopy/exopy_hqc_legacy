# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by EcpyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the capabilities of the AWG5014Context.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from collections import OrderedDict

import enaml
import numpy as np

from ecpy.testing.util import show_and_close_widget

from ecpy_pulses.pulses.sequences.base_sequences import (RootSequence,
                                                         BaseSequence)
from ecpy_pulses.pulses.pulse import Pulse
from ecpy_pulses.pulses.shapes.square_shape import SquareShape
from ecpy_pulses.pulses.shapes.modulation import Modulation

from ecpy_hqc_legacy.pulses.contexts.awg_context import (AWG5014Context,
                                                         to_bytes)
with enaml.imports():
    from ecpy_hqc_legacy.pulses.contexts.views.awg_context_view\
        import AWG5014ContextView


class DummyChannel(object):
    """Dummy AWG channel.

    """
    def __init__(self, driver, index):
        self.array = None
        self.output_state = 'OFF'
        self._driver = driver
        self._index = index

    def select_sequence(self, seq_name):
        self.array = self._driver.sequences[seq_name]

    def clear_sequence(self):
        self.array = None


class DummyDriver(object):
    """Dummy AWG5014Driver used for testing purposes.

    """
    def __init__(self):
        self.sequences = {}
        self.defined_channels = [1, 2, 3, 4]
        self.channels = {i: DummyChannel(self, i) for i in range(1, 5)}
        self.running = False

    def to_send(self, name, array):
        self.sequences[name] = array

    def get_channel(self, ch_id):
        return self.channels[ch_id]


class TestAWGContext(object):
    """Test the AWG5014 context capabilities.

    """
    def setup(self):
        self.root = RootSequence()
        self.context = AWG5014Context(sequence_name='Test')
        self.compile = self.context.compile_and_transfer_sequence
        self.driver = DummyDriver()
        self.root.context = self.context

    def test_changing_unit(self):
        time = self.context.sampling_time
        self.context.time_unit = 'ms'
        assert self.context.sampling_time != time

    def test_compiling_A_pulse_not_selecting(self):
        self.context.select_after_transfer = False
        self.context.run_after_transfer = False
        self.root.time_constrained = True
        self.root.sequence_duration = '1'
        pulse = Pulse(kind='Analogical', shape=SquareShape(amplitude='1.0'),
                      def_1='0.1', def_2='0.5', channel='Ch1_A')
        self.root.add_child_item(0, pulse)

        res, infos, errors = self.compile(self.root, self.driver)
        print(errors)
        assert res
        assert sorted(infos) == sorted(self.context.list_sequence_infos())
        assert not self.driver.running
        assert 'Test_Ch1' in self.driver.sequences
        assert len(self.driver.sequences) == 1
        assert self.driver.channels[1].array is None

        sequence = np.zeros(2000, dtype=np.uint8)
        sequence[1::2] = 2**5
        sequence[201:1001:2] += 2**4 + 2**3 + 4 + 2 + 1
        sequence[200:1000:2] += 255
        np.testing.assert_array_equal(self.driver.sequences['Test_Ch1'],
                                      to_bytes(sequence))

    def test_compiling_M1_pulse_selecting_but_not_clearing(self):
        self.context.clear_unused_channels = False
        self.driver.channels[2].array = np.zeros(10)
        self.context.run_after_transfer = False
        self.root.time_constrained = True
        self.root.sequence_duration = '1'
        pulse = Pulse(kind='Logical', def_1='0.1', def_2='0.5',
                      channel='Ch1_M1')
        pulse2 = Pulse(kind='Logical', def_1='0.1', def_2='0.1',
                       channel='Ch1_M1')
        self.root.add_child_item(0, pulse)
        self.root.add_child_item(1, pulse2)

        res, infos, errors = self.compile(self.root, self.driver)
        print(errors)
        assert res
        assert not self.driver.running
        assert self.driver.channels[2].array is not None
        assert 'Test_Ch1' in self.driver.sequences
        assert len(self.driver.sequences) == 1
        assert (self.driver.channels[1].array is
                self.driver.sequences['Test_Ch1'])

        sequence = np.zeros(2000, dtype=np.uint8)
        sequence[1::2] = 2**5
        sequence[201:1001:2] += 2**6
        np.testing.assert_array_equal(self.driver.channels[1].array,
                                      to_bytes(sequence))

    def test_compiling_M2_pulse_selecting_and_clearing(self):
        self.driver.channels[2].array = np.zeros(10)
        self.context.run_after_transfer = False
        self.root.time_constrained = True
        self.root.sequence_duration = '1'
        pulse = Pulse(kind='Logical', def_1='0.1', def_2='0.5',
                      channel='Ch1_M2')
        self.root.add_child_item(0, pulse)

        res, infos, errors = self.compile(self.root, self.driver)
        print(errors)
        assert res
        assert not self.driver.running
        assert self.driver.channels[2].array is None
        assert 'Test_Ch1' in self.driver.sequences
        assert len(self.driver.sequences) == 1
        assert (self.driver.channels[1].array is
                self.driver.sequences['Test_Ch1'])

    def test_compiling_inverted_logical_pulses_and_running(self):
        self.root.time_constrained = True
        self.root.sequence_duration = '1'
        pulse = Pulse(kind='Logical', def_1='0.1', def_2='0.5',
                      channel='Ch1_M2')
        self.context.inverted_log_channels = ['Ch1_M1', 'Ch1_M2']
        self.root.add_child_item(0, pulse)

        res, infos, errors = self.compile(self.root, self.driver)
        print(errors)
        assert res
        assert self.driver.running
        assert 'Test_Ch1' in self.driver.sequences
        assert len(self.driver.sequences) == 1
        assert (self.driver.channels[1].array is
                self.driver.sequences['Test_Ch1'])

        sequence = np.zeros(2000, dtype=np.uint8)
        sequence[1::2] = 2**7 + 2**6 + 2**5
        sequence[201:1001:2] -= 2**7
        np.testing.assert_array_equal(self.driver.channels[1].array,
                                      to_bytes(sequence))

    def test_compiling_variable_length(self):
        pulse = Pulse(kind='Logical', def_1='0.1', def_2='0.5',
                      channel='Ch1_M1')
        self.context.sampling_frequency = 1e8
        self.root.add_child_item(0, pulse)

        res, infos, errors = self.compile(self.root, self.driver)
        print(errors)
        assert res
        assert self.driver.running
        assert 'Test_Ch1' in self.driver.sequences
        assert len(self.driver.sequences) == 1
        assert (self.driver.channels[1].array is
                self.driver.sequences['Test_Ch1'])

        sequence = np.zeros(100, dtype=np.uint8)
        sequence[1::2] = 2**5
        sequence[21:101:2] += 2**6
        np.testing.assert_array_equal(self.driver.channels[1].array,
                                      to_bytes(sequence))

    def test_too_short_fixed_length(self):
        self.root.time_constrained = True
        self.root.sequence_duration = '0.3'
        pulse = Pulse(kind='Logical', def_1='0.1', def_2='0.5',
                      channel='Ch1_M1')
        self.root.add_child_item(0, pulse)

        res, infos, errors = self.compile(self.root, self.driver)
        print(errors)
        assert not res

    def test_channel_kind_mixing(self):
        pulse = Pulse(kind='Logical', def_1='0.1', def_2='0.5',
                      channel='Ch1_A')
        self.root.add_child_item(0, pulse)

        res, infos, errors = self.compile(self.root, self.driver)
        assert not res

    def test_overlapping_pulses(self):
        self.root.time_constrained = True
        self.root.sequence_duration = '1'
        pulse1 = Pulse(kind='Analogical', def_1='0.1', def_2='0.5',
                       channel='Ch1_A', shape=SquareShape(amplitude='1.0'),
                       modulation=Modulation(frequency='2.5', kind='sin',
                                             activated=True))
        pulse2 = Pulse(kind='Analogical', def_1='0.1', def_2='0.5',
                       channel='Ch1_A', shape=SquareShape(amplitude='1.0'),
                       modulation=Modulation(frequency='2.5', kind='sin',
                                             phase='Pi', activated=True))
        self.root.add_child_item(0, pulse1)
        self.root.add_child_item(1, pulse2)

        res, infos, errors = self.compile(self.root, None)
        print(errors)
        assert res
        assert infos['sequence_ch1'] == 'Test_Ch1'

    def test_nearly_overlapping_M2(self):
        self.root.time_constrained = True
        self.root.sequence_duration = '1'
        pulse1 = Pulse(kind='Logical', def_1='0.1', def_2='0.5',
                       channel='Ch1_M2')
        pulse2 = Pulse(kind='Logical', def_1='0.5', def_2='0.6',
                       channel='Ch1_M2')
        self.root.add_child_item(0, pulse1)
        self.root.add_child_item(1, pulse2)

        res, infos, errors = self.compile(self.root, self.driver)
        print(errors)
        assert res
        assert self.driver.running
        assert 'Test_Ch1' in self.driver.sequences
        assert len(self.driver.sequences) == 1
        assert (self.driver.channels[1].array is
                self.driver.sequences['Test_Ch1'])

        sequence = np.zeros(2000, dtype=np.uint8)
        sequence[1::2] = 2**5
        sequence[201:1201:2] += 2**7
        np.testing.assert_array_equal(self.driver.channels[1].array,
                                      to_bytes(sequence))

    def test_overflow_check_A(self):
        self.root.time_constrained = True
        self.root.sequence_duration = '1'
        pulse1 = Pulse(kind='Analogical', def_1='0.1', def_2='0.5',
                       channel='Ch1_A', shape=SquareShape(amplitude='1.0'),
                       modulation=Modulation(frequency='2.5', kind='sin',
                                             activated=True))
        pulse2 = Pulse(kind='Analogical', def_1='0.1', def_2='0.5',
                       channel='Ch1_A', shape=SquareShape(amplitude='1.0'),
                       modulation=Modulation(frequency='2.5', kind='sin',
                                             activated=True))
        self.root.add_child_item(0, pulse1)
        self.root.add_child_item(1, pulse2)

        res, infos, errors = self.compile(self.root, self.driver)
        print(errors)
        assert not res
        assert 'Ch1_A' in errors

    def test_overflow_check_M1(self):
        self.root.time_constrained = True
        self.root.sequence_duration = '1'
        pulse1 = Pulse(kind='Logical', def_1='0.1', def_2='0.5',
                       channel='Ch1_M1')
        pulse2 = Pulse(kind='Logical', def_1='0.1', def_2='0.5',
                       channel='Ch1_M1')
        self.root.add_child_item(0, pulse1)
        self.root.add_child_item(1, pulse2)

        res, infos, errors = self.compile(self.root, self.driver)
        print(errors)
        assert not res
        assert 'Ch1_M1' in errors

    def test_overflow_check_M2(self):
        self.root.time_constrained = True
        self.root.sequence_duration = '1'
        pulse1 = Pulse(kind='Logical', def_1='0.1', def_2='0.5',
                       channel='Ch1_M2')
        pulse2 = Pulse(kind='Logical', def_1='0.4', def_2='0.6',
                       channel='Ch1_M2')
        self.root.add_child_item(0, pulse1)
        self.root.add_child_item(1, pulse2)

        res, infos, errors = self.compile(self.root, self.driver)
        print(errors)
        assert not res
        assert 'Ch1_M2' in errors

    def test_compiling_sequence1(self):
        self.root.external_vars = OrderedDict({'a': 1.5})

        pulse1 = Pulse(channel='Ch1_M1', def_1='1.0', def_2='{7_start} - 1.0')
        pulse2 = Pulse(channel='Ch1_M2',
                       def_1='{a} + 1.0', def_2='{6_start} + 1.0')
        pulse3 = Pulse(channel='Ch2_M1', def_1='{3_stop} + 0.5', def_2='10.0')
        pulse4 = Pulse(channel='Ch2_M2',
                       def_1='2.0', def_2='0.5', def_mode='Start/Duration')
        pulse5 = Pulse(channel='Ch3_M1',
                       def_1='3.0', def_2='0.5', def_mode='Start/Duration')

        sequence2 = BaseSequence()
        sequence2.add_child_item(0, pulse3)
        sequence1 = BaseSequence()
        for i, item in enumerate([pulse2, sequence2, pulse4]):
            sequence1.add_child_item(i, item)

        for i, item in enumerate([pulse1, sequence1, pulse5]):
            self.root.add_child_item(i, item)

        res, infos, errors = self.compile(self.root, self.driver)
        print(errors)
        assert res
        assert self.driver.running
        for i in (1, 2, 3):
            assert 'Test_Ch%d' % i in self.driver.sequences
        assert len(self.driver.sequences) == 3
        for i in (1, 2, 3):
            assert (self.driver.channels[i].array is
                    self.driver.sequences['Test_Ch%d' % i])


def test_awg5014_context_view(windows):
    """Test displaying the context view.

    """
    root = RootSequence()
    context = AWG5014Context(sequence_name='Test')
    root.context = context
    show_and_close_widget(AWG5014ContextView(context=context, sequence=root))
