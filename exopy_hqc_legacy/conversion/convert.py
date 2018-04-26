# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Routines to update a HQCMeas .ini file to the formats used by exopy.

"""
import os
import shutil
from ast import literal_eval

from configobj import ConfigObj


#: Dependency id for tasks.
TASK_DEP_TYPE = 'exopy.task'

#: Dependency id for task interfaces.
INTERFACE_DEP_TYPE = 'exopy.tasks.interface'

#: Dependency id for the pulse sequences items.
ITEM_DEP_TYPE = 'exopy.pulses.item'

#: Dependency id for the pulse sequences shapes.
SHAPE_DEP_TYPE = 'exopy.pulses.shape'

#: Dependency id for pulse sequence contexts.
CONTEXT_DEP_TYPE = 'exopy.pulses.context'


#: Mapping between task_class (in HQCMeas) and task_id (in exopy)
TASKS = {'ComplexTask': 'exopy.ComplexTask',
         'WhileTask': 'exopy.WhileTask',
         'ConditionalTask': 'exopy.ConditionalTask',
         'BreakTask': 'exopy.BreakTask',
         'ContinueTask': 'exopy.ContinueTask',
         'LoopTask':  'exopy.LoopTask',
         'LogTask': 'exopy.LogTask',
         'DefinitionTask': 'exopy.DefinitionTask',
         'FormulaTask': 'exopy.FormulaTask',
         'SleepTask': 'exopy.SleepTask',
         'ArrayExtremaTask': 'exopy_hqc_legacy.ArrayExtremaTask',
         'ArrayFindValueTask': 'exopy_hqc_legacy.ArrayFindValueTask',
         'SaveTask': 'exopy_hqc_legacy.SaveTask',
         'SaveFileTask': 'exopy_hqc_legacy.SaveFileTask',
         'SaveFileHDF5Task': 'exopy_hqc_legacy.SaveFileHDF5Task',
         'SaveArrayTask': 'exopy_hqc_legacy.SaveArrayTask',
         'LoadArrayTask': 'exopy_hqc_legacy.LoadArrayTask',
         'ApplyMagFieldTask': 'exopy_hqc_legacy.ApplyMagFieldTask',
         'LockInMeasureTask': 'exopy_hqc_legacy.LockInMeasureTask',
         'MeasDCVoltageTask': 'exopy_hqc_legacy.MeasDCVoltageTask',
         'SetRFFrequencyTask': 'exopy_hqc_legacy.SetRFFrequencyTask',
         'SetRFPowerTask': 'exopy_hqc_legacy.SetRFPowerTask',
         'SetRFOnOffTask': 'exopy_hqc_legacy.SetRFOnOffTask',
         'PNASinglePointMeasureTask':
             'exopy_hqc_legacy.PNASinglePointMeasureTask',
         'PNASweepTask': 'exopy_hqc_legacy.PNASweepTask',
         'PNAGetTraces': 'exopy_hqc_legacy.PNAGetTraces',
         'SetDCVoltageTask': 'exopy_hqc_legacy.SetDCVoltageTask',
         'DemodSPTask': 'exopy_hqc_legacy.DemodSPTask',
         'TransferPulseSequenceTask': 'exopy_pulses.TransferPulseSequenceTask'}

#: Mapping between interface_class (in HQCMeas) and interface_id (in exopy)
INTERFACES = {'IterableLoopInterface':
              'exopy.LoopTask:exopy.IterableLoopInterface',
              'LinspaceLoopInterface':
              'exopy.LoopTask:exopy.LinspaceLoopInterface',
              'MultiChannelVoltageSourceInterface':
              ('exopy_hqc_legacy.SetDCVoltageTask:'
               'exopy_hqc_legcy.MultiChannelVoltageSourceInterface'),
              'PNASetRFFrequencyInterface':
              ('exopy_hqc_legacy.SetRFFrequencyTask:'
               'exopy_hqc_legacy.PNASetRFFrequencyInterface'),
              'PNASetRFPowerInterface':
              ('exopy_hqc_legacy.SetRFPowerTask:'
               'exopy_hqc_legacy.PNASetRFPowerInterface'),
              'CSVLoadInterface':
              ('exopy_hqc_legacy.LoadArrayTask:'
               'exopy_hqc_legacy.CSVLoadInterface')}

#: Mapping between item_class (in HQCMeas) and item_id (in exopy_pulses)
ITEMS = {'Pulse': 'exopy_pulses.Pulse',
         'Sequence': 'exopy_pulses.BaseSequence',
         'ConditionalSequence': 'exopy_pulses.ConditionalSequence',
         'RootSequence': 'exopy_pulses.RootSequence'}

#: Mapping between shape_class (in HQCMeas) and shape_id (in exopy_pulses)
SHAPES = {'SquareShape': 'exopy_pulses.SquareShape'}

#: Mapping between context_class (in HQCMeas) and context_id (in exopy_pulses)
CONTEXTS = {'AWGContext': 'exopy_hqc_legacy.AWG5014Context'}

#: Mapping between monitor_class and monitor_id
MONITORS = {'hqc_meas.measure.monitors.text_monitor':
            'exopy.text_monitor'}


def fix_access_exs(task_config, ex, depth):
    """Walk the sections of a task to fix the access exception.

    In HQCMeas access_exs exists only on ComplexTask and can be chained (appear
    at several level). IN Exopy access_exs are stored on the task exporting
    entry in a dict, and the value represents on how many level we should go
    up.

    """
    task_name, entry = ex.split('_')
    for s in task_config.sections:
        s = task_config[s]
        exs = literal_eval(s.get('access_exs', '[]'))
        if ex in exs:
            depth += 1
            del exs[exs.index(ex)]
            s['access_exs'] = repr(exs)
            fix_access_exs(s, ex, depth)
            continue
        elif s.get('task_name') == task_name:
            if (s['task_class'] == 'LoopTask' and
                entry not in ('start', 'stop', 'step', 'points_number',
                              'iterable')):
                depth += 1
                s = s['task']
            exs = literal_eval(s.get('access_exs', '{}'))
            if not isinstance(exs, dict):
                raise RuntimeError('Too deeply nested access-exs.')
            exs[entry] = depth
            s['access_exs'] = repr(exs)
            break


def update_task(task_config):
    """Update the informations about a task.

    Only the task itself is updated not its children or subparts.

    Parameters
    ----------
    task_config : configobj.Section
        Section holding the task infos that should be updated.

    """
    old_id = task_config['task_class']
    if old_id not in TASKS:
        raise ValueError('Unknown or unsupported task found %s' % old_id)
    task_config['task_id'] = TASKS[old_id]
    del task_config['task_class']
    task_config['dep_type'] = TASK_DEP_TYPE
    task_config.rename('task_name', 'name')

    i = 0
    while 'children_task_%d' % i in task_config:
        task_config.rename('children_task_%d' % i, 'children_%d' % i)
        i += 1

    for key in ['selected_driver', 'selected_profile']:
        if key in task_config:
            del task_config[key]

    if 'access_exs' in task_config:
        if task_config['access_exs'] == '[]':
            del task_config['access_exs']
        elif '{' in task_config['access_exs']:
            pass
        else:
            exs = literal_eval(task_config['access_exs'])
            for ex in exs:
                fix_access_exs(task_config, ex, 1)
            if '{' not in task_config['access_exs']:
                del task_config['access_exs']


def update_task_interface(interface_config):
    """Update the informations about a task interface.

    Only the task interface itself is updated not its children or subparts.

    Parameters
    ----------
    interface_config : configobj.Section
        Section holding the task interface infos that should be updated.

    """
    old_id = interface_config['interface_class']
    if old_id in ('AWGTransferInterface', 'TaborTransferInterface'):
        interface_config['__to_clear__'] = True
        return

    if old_id not in INTERFACES:
        raise ValueError('Unknown or unsupported interface found %s' % old_id)
    interface_config['interface_id'] = INTERFACES[old_id]
    del interface_config['interface_class']
    interface_config['dep_type'] = INTERFACE_DEP_TYPE


def update_item(item_config):
    """Update a pulse sequence item.

    """
    old_id = item_config['item_class']
    if old_id not in ITEMS:
        raise ValueError('Unknown or unsupported sequence found %s' % old_id)
    item_config['item_id'] = ITEMS[old_id]
    del item_config['item_class']
    item_config['dep_type'] = ITEM_DEP_TYPE

    if old_id == 'Pulse':
        if 'modulation' in item_config:
            mod = item_config['modulation']
            mod['dep_type'] = 'exopy.pulses.modulation'
            mod['modulation_id'] = 'exopy_pulses.Modulation'


def update_shape(shape_config):
    """Update a pulse shape.

    """
    old_id = shape_config['shape_class']
    if old_id not in SHAPES:
        raise ValueError('Unknown or unsupported shape found %s' % old_id)
    shape_config['shape_id'] = SHAPES[old_id]
    del shape_config['shape_class']
    shape_config['dep_type'] = SHAPE_DEP_TYPE


def update_context(context_config):
    """Update a sequence context.

    """
    old_id = context_config['context_class']
    if old_id not in CONTEXTS:
        raise ValueError('Unknown or unsupported context found %s' % old_id)
    context_config['context_id'] = CONTEXTS[old_id]
    del context_config['context_class']
    context_config['dep_type'] = CONTEXT_DEP_TYPE


def update_monitor(config):
    """Update the informations related to a monitor.

    """
    del config['id']
    if 'measure_name' in config:
        del config['measure_name']
    undisp = literal_eval(config['undisplayed'])
    config['undisplayed'] = repr(undisp + ['meas_name', 'meas_id',
                                           'meas_date'])
    for k in list(config):
        if k.startswith('rule_'):
            del config[k]
        elif k.startswith('custom_'):
            del config[k]

    config['rule_0'] = 'Loop progress'
    config['rule_1'] = 'Measurement entries'


def iterate_on_sections(section, action_mapping):
    """Iterate on section sections and call the appropriate action on each.

    Parameters
    ----------
    section : Section
        Section whose subsections should be walked.

    action_mapping : dict
        Dictionary mapping test functions to callable that should be called if
        the test return True. Both callbale should take as single argument the
        section under inspection.

    """
    for s in list(section.sections):
        s_config = section[s]
        action = None
        for t in action_mapping:
            if t(s_config):
                action = action_mapping[t]
                break
        if action is None:
            raise ValueError('No matching action could be found for %s' % s)
        action(s_config)
        if '__to_clear__' in s_config:
            del section[s]
        iterate_on_sections(s_config, action_mapping)


def convert_measure(meas_path, archive_folder=None, dest_folder=None):
    """Convert a measure created using HQCMeas to make it run on Exopy.

    Parameters
    ----------
    meas_path : unicode
        Path to the file containing the measure to update.

    archive_folder : unicode or None, optional
        Path to the folder in which to store the old file after conversion.

    dest_folder : unicode or None, optional
        Save the new measure into the specified folder

    Returns
    -------
    new_path : unicode
        Location of the new file

    """
    config = ConfigObj(meas_path)

    # Update the main task hierarchy.
    update_task(config['root_task'])
    iterate_on_sections(config['root_task'],
                        {lambda x: 'task_class' in x: update_task,
                         lambda x: 'interface_class' in x:
                             update_task_interface,
                         lambda x: 'item_class' in x: update_item,
                         lambda x: 'shape_class' in x: update_shape,
                         lambda x: 'context_class' in x: update_context,
                         lambda x: 'modulation_id' in x: lambda x: x})

    #: Update the monitors and delete the other non-existing tools
    monitors = {}
    for i in range(int(config['monitors'])):
        m_config = config['monitor_%s' % i]
        if m_config['id'] not in MONITORS:
            raise ValueError('Unknown monitor: %s' % m_config['id'])
        new_id = MONITORS[m_config['id']]
        update_monitor(m_config)
        monitors[new_id] = m_config.dict()
        del config['monitor_%s' % i]

    del config['monitors']
    del config['checks']
    del config['headers']
    config['monitors'] = {}
    config['monitors'].update(monitors)

    if dest_folder:
        new_path = os.path.join(dest_folder,
                                os.path.basename(meas_path)[:-4] + '.meas.ini')
    else:
        new_path = meas_path[:-4] + '.meas.ini'

    with open(new_path, 'wb') as f:
        config.write(f)

    if archive_folder:
        shutil.move(meas_path, archive_folder)

    return new_path
