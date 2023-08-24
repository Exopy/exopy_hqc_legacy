# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""
This is a wrapper module to control Magnet Physik USB hall probe from Python.
The module requires .NET applicatiom package (MagnetPhysik.Usb) to be
installed and to point to MagnetPhysik.Usb.dll in path.
"""

import clr
import atexit

import numpy as np
from inspect import cleandoc
import logging #/!\

from contextlib import contextmanager
from threading import Lock

from ..dotnet_tools import DotNetInstrument
from ..driver_tools import InstrIOError,InstrError,secure_communication

class MagnetPhysik_DotNet_controller(object):
    """ Singleton class used to call the MagnetPhysik_DotNet.

    This class should wrap in python all useful calls to the dotnet, so that the
    driver never needs to access the _instance attribute. All calls to functions here
    (of ._cdotnet of instrument) should be done inside the secure context of the instruments
    below for thread safety. There is one Hall CU (control unit) per detected probe (only simple 
    solution due to availalbe functions), and one overall lock at the DotNet level.
    
    """

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is not None:
            return cls._instance
        else:
            self = super(MagnetPhysik_DotNet_controller, cls).__new__(cls)
            cls._instance = self
            return self

    def __init__(self, library_path, **kwargs):
        clr.AddReference(library_path)
        import MagnetPhysik
        self.timeout = 5.0
        self.lock = Lock()
        if MagnetPhysik_DotNet_controller._initialized == False:
            #Creates a first control unit for probe #0, unique by construction
            self.HallCUs        = [MagnetPhysik.HallProbe()]
            self.InstanceIDs    = [self.HallCUs[0].InstanceID]
            self.InstanceCounts = [self.HallCUs[0].InstanceCount]
            self.Informations   = [self.HallCUs[0].Information]
            self.Names          = [self.HallCUs[0].Name]
            self.SerialNumbers  = [self.HallCUs[0].SerialNumber]
            self.Versions       = [self.HallCUs[0].Version]
            self.HallCUs[0].Reset()
            log = logging.getLogger(__name__)
            msg = ('Instance of DotNet handle is #%s on a total of %s for')
            log.info(msg,str(self.InstanceIDs[0]),str(self.InstanceCounts[0]))
            log.info(self.Informations[0])
            self.SortedbySIDs = {self.SerialNumbers[0]:0}
            self.NOP = self.HallCUs[0].NumberOfProbes
            if self.NOP > 1: #Not tested
                for index in range(1,self.NOP):
                    self.HallCUs        += [MagnetPhysik.HallProbe(index)]
                    self.InstanceIDs    += [self.HallCUs[index].InstanceID]
                    self.InstanceCounts += [self.HallCUs[index].InstanceCount]
                    self.Informations   += [self.HallCUs[index].Information]
                    self.Names          += [self.HallCUs[index].Name]
                    self.SerialNumbers  += [self.HallCUs[index].SerialNumber]
                    self.Versions       += [self.HallCUs[index].Version]
                    log = logging.getLogger(__name__)
                    msg = ('Instance of DotNet handle is #%s on a total of %s for')
                    log.info(msg,str(self.InstanceIDs[index]),str(self.InstanceCounts[index]))
                    log.info(self.Informations[index])
                    self.SortedbySIDs[self.SerialNumbers[index]]=index
            atexit.register(self._cleanup)
            MagnetPhysik_DotNet_controller._initialized = True

    def read_field(self,sid):
            return self.HallCUs[self.SortedbySIDs[sid]].Tesla

    def setup_range(self,sid):
        present_range = self.HallCUs[self.SortedbySIDs[sid]].Range
        if present_range != 6:
            self.HallCUs[self.SortedbySIDs[sid]].Range = 6 ##This is ~2.86T for this probe
        present_range = self.HallCUs[self.SortedbySIDs[sid]].Range
        if present_range != 6:
            raise InstrIOError(cleandoc('''Magnet Physik probe did not set correctly 
                            the range'''))

    def _cleanup(self):
        """Make sure we disconnect all the boards and destroy the unit.

        """
        for index in range(1,self.NOP):
            self._terminate(index)

    def _terminate(self,nid):
            self.HallCUs[nid].Dispose()

class HU_PT1_164005(DotNetInstrument):
    """Driver for the Hall probe

    """

    library = 'MagnetPhysik.Usb'

    def __init__(self, connection_infos, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(HU_PT1_164005, self).__init__(connection_infos, caching_allowed,
                                         caching_permissions, auto_open)
        self._infos = connection_infos
        self._path = self._infos['lib_dir']
        self._id = int(self._infos['instr_id'])

        if auto_open:
            self.open_connection()

    def open_connection(self):
        """Acquire the Hall probe

        """
        self._cdotnet=MagnetPhysik_DotNet_controller(self._path+'\\MagnetPhysik.Usb')

    def reopen_connection(self):
        pass

    @contextmanager
    def secure(self):
        """ Lock acquire and release method.

        """
        t = 0
        while not self._cdotnet.lock.acquire():
            time.sleep(0.1)
            t += 0.1
            log = logging.getLogger(__name__)
            msg = ('Still stuck in lock')
            log.info(msg)
            if t > self._cdotnet.timeout:
                raise InstrIOError('Timeout in trying to acquire MangetPhysik.Usb .NET lock.')
        try:
            yield
        finally:
            self._cdotnet.lock.release()

    @secure_communication()
    def close_connection(self):
        """Release the Hall probe, as instructed in the documentation

        """
        with self.secure():
            pass
            #self._cdotnet.terminate(self._id)

    @secure_communication()
    def read_field(self):
        with self.secure():
            return self._cdotnet.read_field(self._id)

    @secure_communication()
    def setup_dc(self):
        with self.secure():
            self._cdotnet.setup_range(self._id)

    @secure_communication()
    def setup_ac(self):
        raise InstrError(cleandoc('''This MagnetPhysik Hall Probe cannot perform ac
                                    measurements.'''))
