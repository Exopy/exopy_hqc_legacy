# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2022 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task to send parameters to the lock-in.

"""
import time
import logging
import numbers
from inspect import cleandoc

import numpy as np
from atom.api import (Str, Int, Bool, Enum, set_default,
                      Value, List)

from exopy.tasks.api import (InstrumentTask, TaskInterface,
                            InterfaceableTaskMixin, validators)

FEVAL = validators.SkipEmpty(types=numbers.Real)

class SweepLockinTask(InstrumentTask):
    """Record lockin voltage while sweeping a lock in parameter.

    """

    #: Kind of sweep to perform.
    sweep_type = Enum('Frequency', 'Output').tag(pref=True)

    #: Channel to sweep parameter of.
    sweep_channel = Int(default=1).tag(pref=True)

    #: Channel secondary spec.
    sweep_channel_sec = Int(default=1).tag(pref=True)

    #: Measures to perform.
    measures = List().tag(pref=True)

    #: Start value for the sweep.
    start = Str().tag(pref=True, feval=FEVAL)

    #: Stop value for the sweep.
    stop = Str().tag(pref=True, feval=FEVAL)

    #: Number of points desired in the sweep.
    points = Str().tag(pref=True, feval=FEVAL)

    #: Sweep log or linscale
    log_sweep = Bool(False).tag(pref=True)

    #: Avg time per point
    avg_time = Str().tag(pref=True, feval=FEVAL)

    wait = set_default({'activated': True, 'wait': ['instr']})
    database_entries = set_default({'sweep_datadict': {}})

    def prepare(self):
        """Get the channel driver.

        """
        super(SweepLockinTask, self).prepare()

    def perform(self):
        """Set up the measures and run them.

        """
        if self.driver.owner != self.name:
            self.driver.owner = self.name

        driversweeper = self.driver.get_sweeper()

        start=self.format_and_eval_string(self.start)
        stop=self.format_and_eval_string(self.stop)
        points=self.format_and_eval_string(self.points)
        avg_time=self.format_and_eval_string(self.avg_time)

        driversweeper.set_sweep_param(
            self.sweep_type, self.sweep_channel, self.measures, 
            start, stop, points, self.log_sweep, 
            sweep_channel_sec = self.sweep_channel_sec,
            avg_time = avg_time
        )
        driversweeper.sweep_exec()
        while not driversweeper.sweep_finished():
            time.sleep(1)
            if self.root.should_stop.is_set():
                return
        datadict = driversweeper.read_data(
            self.sweep_type, self.sweep_channel, self.measures)
        self.write_in_database('sweep_param', datadict['sweep_param'])
        for (chan,code) in self.measures:
            self.write_in_database(chan+code, datadict[chan+code])        

    def _post_setattr_measures(self, old, new):
        """ Update the database entries acording to the mode.

        """
        entries = {'sweep_param': np.array([0.0])}
        for (chan,code) in new:
            if code=='Raw':
                entries[chan+code] = np.array([0.0 + 0.0j])
            else:
                entries[chan+code] = np.array([0.0])
        self.database_entries = entries

    def check(self, *args, **kwargs):
        """Validate the measures.

        """
        test, traceback = super(SweepLockinTask, self).check(*args, **kwargs)

        #implement a check to avoid twice the same meas
        return test, traceback

class StreamLockinTask(InstrumentTask):
    """Record lockin voltage over timespan.

    """

    #: Measures to perform.
    measures = List().tag(pref=True)

    #: Recording time.
    meastime = Str().tag(pref=True, feval=FEVAL)

    #: Record aux input 1
    record_auxin1 = Bool(False).tag(pref=True)

    #: Record aux input 2
    record_auxin2 = Bool(False).tag(pref=True)

    wait = set_default({'activated': True, 'wait': ['instr']})
    database_entries = set_default({'stream_datadict': {}})

    def prepare(self):
        """Get the channel driver.

        """
        super(StreamLockinTask, self).prepare()

    def perform(self):
        """Set up the measures and run them.

        """
        if self.driver.owner != self.name:
            self.driver.owner = self.name

        driverstreamer = self.driver.get_streamer()

        meastime = self.format_and_eval_string(self.meastime)

        driverstreamer.set_stream_param(self.measures,
                                        meastime,
                                        record_auxin1=self.record_auxin1,
                                        record_auxin2=self.record_auxin2)

        driverstreamer.stream_exec()
        start=time.time()
        while not driverstreamer.stream_finished():
            remainingtime=meastime-(time.time()-start)
            time.sleep(min(min(0.5,meastime),max(0.05,remainingtime)))
            if self.root.should_stop.is_set():
                return
        datadict = driverstreamer.read_data(self.measures,
                                            record_auxin1=self.record_auxin1,
                                            record_auxin2=self.record_auxin2)
        self.write_in_database('sampletime(s)', datadict['sampletime'])
        for (chan,code) in self.measures:
            self.write_in_database(chan+code, datadict[chan+code])
        if self.record_auxin1:
            self.write_in_database('auxin1', datadict['auxin1'])
        if self.record_auxin2:
            self.write_in_database('auxin2', datadict['auxin2'])

    def _post_setattr_measures(self, old, new):
        """ Update the database entries acording to the mode.

        """
        entries = {'sampletime(s)': np.array(1000*[0.0])}
        for (chan,code) in new:
            if code=='Raw':
                entries[chan+code] = np.array(1000*[0.0 + 0.0j])
            else:
                entries[chan+code] = np.array(1000*[0.0])
        if self.record_auxin1:
           entries['auxin1'] = np.array(1000*[0.0])
        if self.record_auxin2:
           entries['auxin2'] = np.array(1000*[0.0])   
        self.database_entries = entries  

    def _post_setattr_record_auxin1(self, old, new):
        """ Update the database entries acording to the mode.

        """
        entries = self.database_entries.copy()
        if new:
            entries['auxin1'] = np.array(1000*[0.0])
        else:
            del entries['auxin1']
        self.database_entries = entries

    def _post_setattr_record_auxin2(self, old, new):
        """ Update the database entries acording to the mode.

        """
        entries = self.database_entries.copy()
        if new:
            entries['auxin2'] = np.array(1000*[0.0])
        else:
            del entries['auxin2']
        self.database_entries = entries

    def check(self, *args, **kwargs):
        """Validate the measures.

        """
        test, traceback = super(StreamLockinTask, self).check(*args, **kwargs)

        #implement a check to avoid twice the same meas
        return test, traceback
