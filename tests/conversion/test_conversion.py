# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the routines to update a HQCMeas .ini file to the formats used by exopy

"""
import os
from traceback import print_exc

import pytest
import enaml
from configobj import ConfigObj

from exopy.measurement.measurement import Measurement
from exopy_hqc_legacy.conversion.convert import (update_task,
                                                 update_task_interface,
                                                 update_monitor,
                                                 iterate_on_sections,
                                                 convert_measure)

with enaml.imports():
    from exopy.tasks.manifest import TasksManagerManifest
    from exopy_hqc_legacy.manifest import HqcLegacyManifest


pytest_plugins = str('exopy.testing.measurement.fixtures'),


def test_update_task():
    """Test updating the informations about a task.

    """
    config = ConfigObj({'task_name': 'decoy',
                        'task_class': 'SetDCVoltageTask',
                        'selected_driver': None,
                        'selected_profile': None,
                        'voltage': '1.0'})
    update_task(config)
    assert 'task_class' not in config
    assert config['task_id'] == 'exopy_hqc_legacy.SetDCVoltageTask'
    assert 'dep_type' in config
    assert 'selected_driver' not in config
    assert 'selected_profile' not in config
    assert 'voltage' in config

    with pytest.raises(ValueError):
        config = {'task_class': '__dummy__'}
        update_task(config)


def test_update_task_interface():
    """Test updating the informations about a task interface.

    """
    config = {'interface_class': 'IterableLoopInterface',
              'iterable': '[]'}
    update_task_interface(config)
    assert 'interface_class' not in config
    assert (config['interface_id'] ==
            'exopy.LoopTask:exopy.IterableLoopInterface')
    assert 'dep_type' in config
    assert 'iterable' in config

    with pytest.raises(ValueError):
        config = {'interface_class': '__dummy__'}
        update_task_interface(config)


# XXX add tests for the new update functions


def test_update_monitor():
    """Test updating the informations related to a monitor.

    """
    config = {'id': None, 'undisplayed': '[]', 'rule_0': {},
              'custom_0': {}}
    update_monitor(config)

    assert 'id' not in config
    assert config['undisplayed'] == repr(['meas_name', 'meas_id', 'meas_date'])
    assert config['rule_0'] == 'Loop progress'
    assert 'custom_0' not in config


def test_iterate_on_sections():
    """Test iterating on section sections

    """
    section = ConfigObj()
    section['a'] = {'val1': None}
    section['b'] = {'val2': None}
    section['b']['c'] = {'val3': None}

    class Checker(object):

        __slots__ = ('called')

        def __call__(self, section):
            self.called = True

    check1, check2 = Checker(), Checker()
    actions = {lambda x: 'val1' in x: check1, lambda x: 'val2' in x: check2}

    with pytest.raises(ValueError):
        iterate_on_sections(section, actions)

    assert check1.called
    assert check2.called


MEASURE_DIRECTORY = os.path.join(os.path.dirname(__file__), 'test_measures')


MEASURES_FILES = [
    'Avg_FreqCav.ini',
    'Bfield_cav.ini',
    'Bfield-Gate_IPhA_hysteres.ini',
    'Bfield_IPhA_hysteres.ini',
    'Eps-Bfield_PhA_oneway.ini',
    pytest.mark.xfail('FastGateCal_PhA.ini'),
    'Find-Set_fc_avg.ini',
    'Find-Set_fc_Hetero-LockIn.ini',
    'Find-Set_fc_Hetero-LockIn_TestEXG.ini',
    'Find-Set_fc.ini',
    'Find-Set_fc_SPCard.ini',
    'Gate-Bfield_IPhA_oneway.ini',
    'Gate-Bfield_PhA_oneway.ini',
    'Gate-Power-Frequence_PhA.ini',
    'Gate-Power_PhA.ini',
    'Gate-Spectro_ON-OFF_IPhA.ini',
    'Gate-Spectro_ON-OFF_PhA.ini',
    'GotoField.ini',
    'GrayscaleAlphaEpsilon.ini',
    'GrayscaleAlphaEpsilon-Skewed.ini',
    'GrayScale_Current.ini',
    'GrayScale_IPhA_Hetero-LockIn.ini',
    'GrayScale_IPhA.ini',
    'GrayScale_IPhA_SPCard.ini',
    'GrayScale_multi_PhA.ini',
    'GrayScale_PhA_Hetero-LockIn_cav_pulsed.ini',
    'GrayScale_PhA_Hetero-LockIn.ini',
    'GrayScale_PhA_Hetero-LockIn_TestEXG.ini',
    'GrayScale_PhA_Hetero-LockInTK.ini',
    'GrayScale_PhA.ini',
    'GrayScale_PhA_SPCard_good.ini',
    'GrayScale_PhA_SP.ini',
    'GrayScale_PhA_SP_Vgt.ini',
    'GrayScale_PhA_Vsd.ini',
    'GrayScale_Vgt_PhA_Hetero-LockIn.ini',
    'Power_scancav.ini',
    'RFspectroCAL_Freq-Avg_IPhA.ini',
    'RFspectroCAL_Freq-Gate_IPhA.ini',
    'RFspectroCAL_Freq-Gate_PhA.ini',
    'RFspectroCAL_Gate-Freq_PhA.ini',
    'RFspectro_Eps-Freq_PhA.ini',
    'RFspectro_Freq-Avg_I_Harmonics.ini',
    'RFspectro_Freq-Avg_IPhA.ini',
    'RFspectro_Freq-B_I.ini',
    'RFspectro_Freq-CavPower_PhA.ini',
    'RFspectro_Freq-Gate_IPhA.ini',
    'RFspectro_Freq-Gate_PhA_aroundcav.ini',
    'RFspectro_Freq-Gate_PhA_belowcav.ini',
    'RFspectro_Freq-Gate_PhA.ini',
    'RFspectro_Freq-Gate_PhA_SP_cont.ini',
    'RFspectro_Freq-Gate_PhA_SP_pulsed.ini',
    'RFspectro_Freq-Power_I-PhA.ini',
    'RFspectro_Freq-Power_PhA.ini',
    'RFspectro_Gate-Freq_PhA.ini',
    'Scan-Cav_Hetero-LockIn.ini',
    'Scan-Cav_Hetero-LockIn_pulsed.ini',
    'Scan_cav_SPCard.ini',
    'Spectro-Bfield_IPhA_oneway.ini',
    'Spectro-Bfield_PhA_aroundfc.ini',
    'Spectro-Bfield_PhA_oneway.ini',
    'Spectro_gate-Freq_ON-OFF_PhA.ini',
    'Spectro_gate-Freq_ON-OFF_PhA_PNA.ini',
    'Spectro_gate-Freq_PhA_PNA.ini',
    'Spectro_gate-Power_Freq_PhA_PNA.ini',
    'Spectro_ON-OFF_PhA.ini',
    'Spectro_Power-Freq_ON-OFF_PhA.ini',
    'Spectro_Power-Freq_ON-OFF_PhA_PNA.ini',
    'Spectro_Power-Freq_PhA_PNA.ini',
    'Spectro_Power-Freq_PhA_SP.ini',
    'Sweep_2_sources.ini',
    'SweepBfield_FreqCav-Gate.ini',
    'SweepBfield_FreqCav.ini',
    'SweepBfield_Gate.ini',
    'SweepBfield.ini',
    'SweepBfield_multipleGates_IPhA.ini',
    'SweepEps_FreqCav.ini',
    'SweepEps_PhA.ini',
    'SweepFreq-Gate-Bfield_PhA.ini',
    'SweepFreq-Gate_PhA.ini',
    pytest.mark.xfail('SweepGate_FastGateTest_IphA.ini'),
    'SweepGate_FastGateTest_PSG_IphA.ini',
    pytest.mark.xfail('SweepGate_FastGate_Vg2Vg1_IphA.ini'),
    'SweepGate_FreqCav.ini',
    'SweepGate_FreqCav+spectro.ini',
    'SweepGate_IPhA_Hetero-LockIn.ini',
    'SweepGate_IphA.ini',
    'SweepGate_Keithley.ini',
    'SweepGate_ParaAmpTest_PSG_IphA.ini',
    'SweepGate_ParaAmpTest_Vg1Vsd_PSG_IphA.ini',
    'SweepGate_PhA_CavPulsed.ini',
    'SweepGate_PhA_Hetero-LockIn.ini',
    'SweepGate_PhA.ini',
    'SweepGate_PhA_SP.ini',
    'Sweep-PowerEps_PhA.ini',
    'SweepPower_FreqCav.ini',
    'SweepPower-Freq_I.ini',
    'SweepPowerGate_PhA_SP.ini',
    'SweepPower_GrayScale_PhA_SP.ini',
    'SweepPower_I.ini',
    'Sweep-Skewed-PowerEps_PhA.ini',
    'Time_SPCard.ini',
    'transfer_sequence.ini',
    'Vsd_GrayScale_PhA.ini',
]


@pytest.mark.parametrize('meas_file', MEASURES_FILES)
def test_converting_a_measurement(measurement_workbench, meas_file, tmpdir,
                                  monkeypatch):
    """Test converting a measurement created using HQCMeas to make it run on
    Exopy.

    """
    import enaml
    from exopy.measurement.monitors.text_monitor import monitor
    monkeypatch.setattr(monitor, 'information', lambda *args, **kwargs: 1)
    measurement_workbench.register(TasksManagerManifest())
    measurement_workbench.register(HqcLegacyManifest())
    try:
        with enaml.imports():
            from exopy_pulses.pulses.manifest import PulsesManagerManifest
            measurement_workbench.register(PulsesManagerManifest())
            from exopy_pulses.tasks.manifest import PulsesTasksManifest
            measurement_workbench.register(PulsesTasksManifest())
            from exopy_hqc_legacy.pulses.manifest\
                import HqcLegacyPulsesManifest
            measurement_workbench.register(HqcLegacyPulsesManifest())
    except ImportError:
        print('Exopy pulses is not installed')
        print_exc()

    plugin = measurement_workbench.get_plugin('exopy.measurement')

    path = convert_measure(os.path.join(MEASURE_DIRECTORY, meas_file),
                           dest_folder=str(tmpdir))

    res, errors = Measurement.load(plugin, path)
    with open(path) as f:
        print(errors.get('main task'), f.read())
    assert res
