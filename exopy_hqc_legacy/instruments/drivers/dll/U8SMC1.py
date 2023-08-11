# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""
This is a wrapper module to control Standa 8SMC1-USBhF stepper motor
controllers (http://www.standa.lt/products/catalog/motorised_positioners?item=175)
from Python. The module requires C/C++ developement package (MicroSMC) to be
installed and to point to USMCDLL.dll in path.
"""

import os
import sys
import time
import atexit

import ctypes
from ctypes import wintypes
import pyclibrary

import numpy as np
import logging #/!\

from contextlib import contextmanager
from threading import Lock

from inspect import cleandoc

from ..dll_tools import DllInstrument
from ..driver_tools import (InstrIOError, secure_communication,
                            instrument_property)

#########################
#### CPython attempt ####
#########################

#===============================================================================
# Helper structures
#===============================================================================

class _SettingsBase(ctypes.Structure):
    """Helper base class for  simplifying the setting and updating the settings.
    
    Parameters
    ----------
    motor : `Motor`
        Instance of the motor whose settings are being controlled.
        
    """


    def __init__(self):
        ctypes.Structure.__init__(self)
        
    def Set(self, **kwargs):
        """Helper function to set parameters. Sam functionality could be
        achived also by modifying the member and then calling `Apply` method. 
        
        """
        allowedKeys, _ = zip(*self._fields_)
        for key, value in kwargs.items():
            if not key in allowedKeys:
                raise Exception("No such key %s in %s" % (key, self))
            self._fields_.__setattr__(key, value)
        
    def Get(self, variable):
        """Helper method to get latest value of `variable`. Internally calls
        `Refresh` method and then returns the value.
        
        Returns
        -------
        The value of the `variable`.
        
        """
        allowedKeys, _ = zip(*self._fields_)
        if not variable in allowedKeys:
            raise ValueError("No such key %s in %s" % (variable, self))
        return getattr(self._fields_, variable)

    def __str__(self):
        res = ["---Settings---:"]
        for member, _ in self._fields_:
            res.append("%s = %s" % (member, getattr(self, member)))
        return "\n".join(res)

class USMC_Devices(ctypes.Structure):
    """Wrapper class for USMC_Devices structure.
    
    Attributes
    ----------
    NOD : int
        Number of stepper motor controllers (axes).
    Serial : list of strings
        List containing the serial numbers of all controllers.
    Version : list of string
        List containing the version number of all controllers.
    
    """
    _fields_ = [
        ("NOD", wintypes.DWORD),
        ("Serial", ctypes.POINTER(ctypes.c_char_p)),
        ("Version", ctypes.POINTER(ctypes.c_char_p)),
        ]

class USMC_Parameters(_SettingsBase):
    """Wrapper class for `USMC_Parameters` structure.
    
    Attributes
    ----------
        See the user manual of the controller
        http://www.standa.lt/files/usb/8SMC1-USBhF%20User%20Manual.pdf
    
    """
    _fields_ = [
        ("AccelT", ctypes.c_float),
        ("DecelT", ctypes.c_float),
        ("PTimeout", ctypes.c_float),
        ("BTimeout1", ctypes.c_float),
        ("BTimeout2", ctypes.c_float),
        ("BTimeout3", ctypes.c_float),
        ("BTimeout4", ctypes.c_float),
        ("BTimeoutR", ctypes.c_float),
        ("BTimeoutD", ctypes.c_float),
        ("MinP", ctypes.c_float),
        ("BTO1P", ctypes.c_float),
        ("BTO2P", ctypes.c_float),
        ("BTO3P", ctypes.c_float),
        ("BTO4P", ctypes.c_float),
        ("MaxLoft", wintypes.WORD),
        ("StartPos", wintypes.DWORD),
        ("RTDelta", wintypes.WORD),
        ("RTMinError", wintypes.WORD),
        ("MaxTemp", ctypes.c_float),
        ("SynOUTP", wintypes.BYTE),
        ("LoftPeriod", ctypes.c_float),
        ("EncMult", ctypes.c_float),
        ("Reserved", wintypes.BYTE * 16),
        ]

class USMC_StartParameters(_SettingsBase):
    """Wrapper class for `USMC_StartParameters` structure.
    
    Attributes
    ----------
        See the user manual of the controller
        http://www.standa.lt/files/usb/8SMC1-USBhF%20User%20Manual.pdf
    
    """
    _fields_ = [
        ("SDivisor", wintypes.BYTE),
        ("DefDir", wintypes.BOOL),
        ("LoftEn", wintypes.BOOL),
        ("SlStart", wintypes.BOOL),
        ("WSyncIN", wintypes.BOOL),
        ("SyncOUTR", wintypes.BOOL),
        ("ForceLoft", wintypes.BOOL),
        ("Reserved", wintypes.BOOL * 4),
        ]

class USMC_Mode(_SettingsBase):
    """Wrapper class for `USMC_Mode` structure.
    
    Attributes
    ----------
        See the user manual of the controller
        http://www.standa.lt/files/usb/8SMC1-USBhF%20User%20Manual.pdf
    
    """
    _fields_ = [
        ("PMode", wintypes.BOOL),
        ("PReg", wintypes.BOOL),
        ("ResetD", wintypes.BOOL),
        ("EMReset", wintypes.BOOL),
        ("Tr1T", wintypes.BOOL),
        ("Tr2T", wintypes.BOOL),
        ("RotTrT", wintypes.BOOL),
        ("TrSwap", wintypes.BOOL),
        ("Tr1En", wintypes.BOOL),
        ("Tr2En", wintypes.BOOL),
        ("RotTeEn", wintypes.BOOL),
        ("RotTrOp", wintypes.BOOL),
        ("Butt1T", wintypes.BOOL),
        ("Butt2T", wintypes.BOOL),
        ("ResetRT", wintypes.BOOL),
        ("SyncOUTEn", wintypes.BOOL),
        ("SyncOUTR", wintypes.BOOL),
        ("SyncINOp", wintypes.BOOL),
        ("SyncCount", wintypes.DWORD),
        ("SyncInvert", wintypes.BOOL),
        ("EncoderEn", wintypes.BOOL),
        ("EncoderInv", wintypes.BOOL),
        ("ResBEnc", wintypes.BOOL),
        ("ResEnc", wintypes.BOOL),
        ("Reserved", wintypes.BYTE * 8),
        ]
    
class USMC_State(_SettingsBase):
    """Wrapper class for `USMC_State` structure.
    
    Attributes
    ----------
        See the user manual of the controller
        http://www.standa.lt/files/usb/8SMC1-USBhF%20User%20Manual.pdf
    
    """
    _fields_ = [
        ("CurPos", ctypes.c_int),
        ("Temp", ctypes.c_float),
        ("SDivisor", wintypes.BYTE),
        ("Loft", wintypes.BOOL),
        ("FullPower", wintypes.BOOL),
        ("CW_CCW", wintypes.BOOL),
        ("Power", wintypes.BOOL),
        ("FullSpeed", wintypes.BOOL),
        ("AReset", wintypes.BOOL),
        ("RUN", wintypes.BOOL),
        ("SyncIN", wintypes.BOOL),
        ("SyncOUT", wintypes.BOOL),
        ("RotTr", wintypes.BOOL),
        ("RotTrErr", wintypes.BOOL),
        ("EmReset", wintypes.BOOL),
        ("Trailer1", wintypes.BOOL),
        ("Trailer2", wintypes.BOOL),
        ("Voltage", ctypes.c_float),
        ("Reserved", wintypes.BYTE * 8),
        ]

class USMC_EncoderState(_SettingsBase):
    """Wrapper class for `USMC_EncoderState` structure.
    
    Attributes
    ----------
        See the user manual of the controller
        http://www.standa.lt/files/usb/8SMC1-USBhF%20User%20Manual.pdf
    
    """
    _fields_ = [
        ("EncoderPos", ctypes.c_int),
        ("ECurPos", ctypes.c_int),
        ("Reserved", wintypes.BYTE * 8),
        ]

class USMC_Info(_SettingsBase):
    """Wrapper class for `USMC_Info` structure.
    
    Attributes
    ----------
        See the user manual of the controller
        http://www.standa.lt/files/usb/8SMC1-USBhF%20User%20Manual.pdf
    
    """
    _fields_ = [
        ("serial", ctypes.c_char * 17),
        ("dwVersion", wintypes.DWORD),
        ("DevName", ctypes.c_char * 32),
        ("CurPos", ctypes.c_int),
        ("DestPos", ctypes.c_int),
        ("Speed", ctypes.c_float),
        ("ErrState", wintypes.BOOL),
        ("Reserved", wintypes.BYTE * 16),
        ]

class USMC_CTypes_Dll(object):
    """ Singleton class used to call the USMC dll.

    This class should wrap in python all useful call to the dll, so that the
    driver never need to access the _instance attribute. All manipulation of
    the dll should be done inside the secure context for thread safety.

    Only for Windows now

    Parameters
    ----------

    timeout : float, optional
        Timeout to use when attempting to acquire the library lock.

    This main class connects to USMCDLL.dll module and initializes the required 
    (= not all) motors. By default, all motors are assumed to be rotational stages
    Standa 8MR190-2, however it could be reconfigured by `position` attribute
    of the `Motor` class.

    Attributes
    ----------
    N : int
        Number of motors.
    motors : list
        List of instances to `USMC_Motor` class
    N_req : int
        Number of motors requested for control.
    motors_req : list
        List of instances to `USMC_Motor` class requested for control.
    
    """

    _instance = None

    def __new__(cls, infos, **kwargs):
        if cls._instance is not None:
            return cls._instance
        else:
            self = super(USMC_CTypes_Dll, cls).__new__(cls)

            # try:
            #     if sys.platform == 'win32':
            #         log = logging.getLogger(__name__)
            #         msg = ('Killing .exe directly')
            #         log.info(msg)
            #         #call("TASKKILL /F /IM MicroSMC.exe", shell=True)
            #         time.sleep(0.1)
            # except Exception:
            #     pass

            library_path = os.path.join(infos.get('lib_dir', ''),
                                       'USMCDLL.dll')

            log = logging.getLogger(__name__)
            msg = ('Calling C lib for USMC controller at %s')
            log.info(msg, library_path)

            self._dll = ctypes.WinDLL(library_path)
            self._dll_handle = self._dll._handle
            self.kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            self.kernel32.FreeLibrary.argtypes = [wintypes.HMODULE]

            log = logging.getLogger(__name__)
            msg = ('Loaded %s at handle %s')
            log.info(msg, str(self._dll), str(self._dll_handle))

            self._dll.USMC_Init.argtypes = [ctypes.POINTER(USMC_Devices)]
            self._dll.USMC_Init.restype = wintypes.DWORD
            
            self._dll.USMC_GetState.argtypes = [wintypes.DWORD, ctypes.POINTER(USMC_State)]
            self._dll.USMC_GetState.restype = wintypes.DWORD
            
            self._dll.USMC_SaveParametersToFlash.argtypes = [wintypes.DWORD]
            self._dll.USMC_SaveParametersToFlash.restype = wintypes.DWORD
            
            self._dll.USMC_SetCurrentPosition.argtypes = [wintypes.DWORD, ctypes.c_int]
            self._dll.USMC_SetCurrentPosition.restype = wintypes.DWORD
            
            self._dll.USMC_GetMode.argtypes = [wintypes.DWORD, ctypes.POINTER(USMC_Mode)]
            self._dll.USMC_GetMode.restype = wintypes.DWORD
            
            self._dll.USMC_SetMode.argtypes = [wintypes.DWORD, ctypes.POINTER(USMC_Mode)]
            self._dll.USMC_SetMode.restype = wintypes.DWORD
            
            self._dll.USMC_GetParameters.argtypes = [wintypes.DWORD, ctypes.POINTER(USMC_Parameters)]
            self._dll.USMC_GetParameters.restype = wintypes.DWORD
            
            self._dll.USMC_SetParameters.argtypes = [wintypes.DWORD, ctypes.POINTER(USMC_Parameters)]
            self._dll.USMC_SetParameters.restype = wintypes.DWORD
            
            self._dll.USMC_GetStartParameters.argtypes = [wintypes.DWORD, ctypes.POINTER(USMC_StartParameters)]
            self._dll.USMC_GetStartParameters.restype = wintypes.DWORD
            
            self._dll.USMC_Start.argtypes = [wintypes.DWORD, ctypes.c_int, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(USMC_StartParameters)]
            self._dll.USMC_Start.restype = wintypes.DWORD
            
            self._dll.USMC_Stop.argtypes = [wintypes.DWORD]
            self._dll.USMC_Stop.restype = wintypes.DWORD
            
            self._dll.USMC_GetLastErr.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
            
            self._dll.USMC_Close.argtypes = []
            self._dll.USMC_Close.restype = wintypes.DWORD
            
            self._dll.USMC_GetEncoderState.argtypes = [wintypes.DWORD, ctypes.POINTER(USMC_EncoderState)]
            self._dll.USMC_GetEncoderState.restype = wintypes.DWORD

            self.timeout = kwargs.get('timeout', 5.0)
            self.lock = Lock()

            cls._instance = self
            return self

    @contextmanager
    def secure(self):
        """ Lock acquire and release method.

        """
        t = 0
        while not self.lock.acquire():
            time.sleep(0.1)
            t += 0.1
            if t > self.timeout:
                raise InstrIOError('Timeout in trying to acquire dll lock.')
        try:
            yield
        finally:
            self.lock.release()

    def process_error_code(self, errCode):
        """Helper function to postprocess the error codes. If error code is not
        0, the RuntimeError is raised.
        
        """
        errorStr = ctypes.create_string_buffer(100)
        self._dll.USMC_GetLastErr(errorStr, len(errorStr))
        log = logging.getLogger(__name__)
        log.info("Error code: %d, %s" % (errCode, errorStr.value))
        return ("Error code: %d, %s" % (errCode, errorStr.value))

    def get_connected_devices_dll(self):
        devices = USMC_Devices()
        errorcode = self._dll.USMC_Init(devices)
        if errorcode != 0:
            raise InstrIOError(cleandoc('Controller returned {} at connection'
                                          .format(self.process_error_code(errorcode))))

        N = devices.NOD
        serials = []
        for i in range(N):
            serials.append(devices.Serial[i])
        return N,serials

    def get_present_state_dll(self,motor_index):
        # To obtain present information (state incl. pos and motion) on a motor
        state = USMC_State()
        errorcode = self._dll.USMC_GetState(motor_index,state)
        if errorcode != 0:
            raise InstrIOError(cleandoc('Controller returned {} when accessing state'
                                          .format(self.process_error_code(errorcode))))
        return state

    def get_present_mode_dll(self,motor_index):
        mode = USMC_Mode()
        errorcode = self._dll.USMC_GetMode(motor_index,mode)
        if errorcode != 0:
            raise InstrIOError(cleandoc('Controller returned {} when accessing mode'
                                          .format(self.process_error_code(errorcode))))
        return mode

    def set_present_mode_dll(self,motor_index,mode):
        errorcode = self._dll.USMC_SetMode(motor_index,mode)
        if errorcode != 0:
            raise InstrIOError(cleandoc('Controller returned {} when writing mode'
                                          .format(self.process_error_code(errorcode))))

    def get_present_params_dll(self,motor_index):
        params = USMC_Parameters()
        errorcode = self._dll.USMC_GetParameters(motor_index,params)
        if errorcode != 0:
            raise InstrIOError(cleandoc('Controller returned {} when accessing params'
                                          .format(self.process_error_code(errorcode))))
        return params

    def set_present_params_dll(self,motor_index,params):
        errorcode = self._dll.USMC_SetParameters(motor_index,params)
        if errorcode != 0:
            raise InstrIOError(cleandoc('Controller returned {} when writing params'
                                          .format(self.process_error_code(errorcode))))

    def get_start_params_dll(self,motor_index):
        startp = USMC_StartParameters()
        errorcode = self._dll.USMC_GetStartParameters(motor_index,startp)
        if errorcode != 0:
            raise InstrIOError(cleandoc('Controller returned {} when accessing start params'
                                          .format(self.process_error_code(errorcode))))
        return startp

    def start_motion_dll(self,motor_index,destination,speed_floatptr,startp):
        errorcode = self._dll.USMC_Start(motor_index,destination,speed_floatptr,startp)
        if errorcode != 0:
            raise InstrIOError(cleandoc('Controller returned {} when starting motor'
                                          .format(self.process_error_code(errorcode))))

    def stop_motion_dll(self,motor_index):
        errorcode = self._dll.USMC_Stop(motor_index)
        if errorcode != 0:
            raise InstrIOError(cleandoc('Controller returned {} when stopping motor'
                                          .format(self.process_error_code(errorcode))))

    def close_dll(self):
        log = logging.getLogger(__name__)
        msg = ('Killing with Close, still %s inst')
        log.info(msg,sys.getrefcount(self))
        self._dll.USMC_Close()
        del self._dll
        self.kernel32.FreeLibrary(self._dll_handle)
        self.__class__._instance = None

############################
#### PyCLibrary attempt ####
############################

class USMC_PyClib_Dll(object):
    """ Singleton class used to call the USMC dll.

    This class should wrap in python all useful call to the dll, so that the
    driver never need to access the _instance attribute. All manipulation of
    the dll should be done inside the secure context for thread safety.

    Parameters
    ----------

    timeout : float, optional
        Timeout to use when attempting to acquire the library lock.

    This main class connects to USMCDLL.dll module and initializes the required 
    (= not all) motors. By default, all motors are assumed to be rotational stages
    Standa 8MR190-2, however it could be reconfigured by `position` attribute
    of the `Motor` class.

    Attributes
    ----------
    N : int
        Number of motors.
    motors : list
        List of instances to `USMC_Motor` class
    N_req : int
        Number of motors requested for control.
    motors_req : list
        List of instances to `USMC_Motor` class requested for control.
    
    """

    _instance = None

    def __new__(cls, infos, **kwargs):
        if cls._instance is not None:
            return cls._instance
        self = super(USMC_PyClib_Dll, cls).__new__(cls)

        cache_path = os.path.join(os.path.dirname(__file__),
                                      '8SMC1.pycctypes.libc')
        library_path = os.path.join(infos.get('lib_dir', ''),
                                   'USMCDLL.dll')
        header_path = os.path.join(infos.get('header_dir', ''),
                                  'USMCDLL.h')
        windefs = pyclibrary.win_defs()

#        log = logging.getLogger(__name__)
#        msg = ('Allowed wintypes are {}')
#        log.info(msg,print(windefs))

        def replace_WORD(matchobject):
            return matchobject.group(0)[:-4]+"UINT16"        

        headers = pyclibrary.CParser([header_path], copy_from=windefs, replace={
            "DWORD":"DWORD32",
            "BYTE":"TBYTE",
            "BOOL":"bool",
            r"\WWORD":replace_WORD,
            "size_t":"SIZE_T"
        })

#        log = logging.getLogger(__name__)
#        msg = ('Loaded headers are {}')
#        log.info(msg,print(headers))

        log = logging.getLogger(__name__)
        msg = ('Calling C lib for USMC controller')
        log.info(msg)

        self._dll = pyclibrary.CLibrary(library_path, headers, cache=cache_path,
                             prefix=['USMC',  'USMC_'], convention='windll', backend='ctypes')

        self.timeout = kwargs.get('timeout', 5.0)
        self.lock = Lock()

        cls._instance = self
        return self

    @contextmanager
    def secure(self):
        """ Lock acquire and release method.

        """
        t = 0
        while not self.lock.acquire():
            time.sleep(0.1)
            t += 0.1
            if t > self.timeout:
                raise InstrIOError('Timeout in trying to acquire dll lock.')
        try:
            yield
        finally:
            self.lock.release()

    def process_error_code(self, errCode):
        """Helper function to postprocess the error codes. If error code is not
        0, the RuntimeError is raised.
        
        """
        errorStr = ctypes.create_string_buffer(100)
        self._dll.USMC_GetLastErr(errorStr, len(errorStr))
        return ("Error code: %d, %s" % (errCode, errorStr.value))

    def get_connected_devices_dll(self):
        devices = self._dll.USMC_Devices()
        errorcode = self._dll.USMC_Init(devices)
        if errorcode() != 0:
            raise InstrIOError(cleandoc('Controller returned {} at connection'
                                          .format(self.process_error_code(errorcode()))))
        N = devices.NOD
        serials = []
        for i in range(N):
            serials.append(devices.Serial[i])
        return N,serials

    def get_present_state_dll(self,motor_index):
        # To obtain present information (state incl. pos and motion) on a motor
        state = self._dll.USMC_State()
        errorcode = self._dll.USMC_GetState(motor_index,state)
        if errorcode() != 0:
            raise InstrIOError(cleandoc('Controller returned {} when accessing state'
                                          .format(self.process_error_code(errorcode()))))
        return state

    def get_present_mode_dll(self,motor_index):
        mode = self._dll.USMC_Mode()
        errorcode = self._dll.USMC_GetMode(motor_index,mode)
        if errorcode() != 0:
            raise InstrIOError(cleandoc('Controller returned {} when accessing mode'
                                          .format(self.process_error_code(errorcode()))))
        return mode

    def set_present_mode_dll(self,motor_index,mode):
        errorcode = self._dll.USMC_SetMode(motor_index,mode)
        if errorcode() != 0:
            raise InstrIOError(cleandoc('Controller returned {} when writing mode'
                                          .format(self.process_error_code(errorcode()))))

    def get_present_params_dll(self,motor_index):
        params = self._dll.USMC_Parameters()
        errorcode = self._dll.USMC_GetParameters(motor_index,params)
        if errorcode() != 0:
            raise InstrIOError(cleandoc('Controller returned {} when accessing params'
                                          .format(self.process_error_code(errorcode()))))
        return params

    def set_present_params_dll(self,motor_index,params):
        errorcode = self._dll.USMC_SetParameters(motor_index,params)
        if errorcode() != 0:
            raise InstrIOError(cleandoc('Controller returned {} when writing params'
                                          .format(self.process_error_code(errorcode()))))

    def get_start_params_dll(self,motor_index):
        startp = self.library.USMC_StartParameters()
        errorcode = self._dll.USMC_GetStartParameters(motor_index,startp)
        if errorcode() != 0:
            raise InstrIOError(cleandoc('Controller returned {} when accessing start params'
                                          .format(self.process_error_code(errorcode()))))
        return startp

    def start_motion_dll(self,motor_index,destination,speed_floatptr,startp):
        errorcode = self._dll.USMC_Start(motor_index,destination,speed_floatptr,startp)
        if errorcode() != 0:
            raise InstrIOError(cleandoc('Controller returned {} when starting motor'
                                          .format(self.process_error_code(errorcode()))))

    def stop_motion_dll(self,motor_index):
        errorcode = self._dll.USMC_Stop(motor_index)
        if errorcode() != 0:
            raise InstrIOError(cleandoc('Controller returned {} when stopping motor'
                                          .format(self.process_error_code(errorcode()))))

    def close_dll(self):
        log = logging.getLogger(__name__)
        msg = ('Killing with Close, still {} inst')
        log.info(msg,sys.getrefcount(self))
        self._dll.USMC_Close()
        self.__class__._instance = None

###########################################
##### Controller interacting with DLL #####
###########################################

class USMC_Controller(object):
    """
    Class for controlling all motors. By default a 1 axis stage 
    is asssumed. This class initializes a single instance of the 
    `dll` class at a time with open_controller.
    """


    def __init__(self, connection_infos):
        super(USMC_Controller, self).__init__()
        self.infos = connection_infos
        #atexit.register(self._cleanup)

    def open_library(self):
        self.library = USMC_CTypes_Dll(self.infos) ## Change here to try one C library or the other
        with self.library.secure():
            self.N, self.serials = self.library.get_connected_devices_dll()
        self.N_req = 0
        self.serials_req = []

        log = logging.getLogger(__name__)
        msg = ('Motors found are %s in total, %s')
        log.info(msg,str(self.N),';'.join([str(bserial, 'ascii') for bserial in self.serials]))

        self.step_resolution = 8 #Now used as a global param of all motors for simplicity

    def get_motors_serials(self):
        return self.serials

    def request_motor(self,serial):
        # Add motor to list of used devices and returns its num index for easy adressing
        bserial = bytes(serial, 'ascii')
        if bserial in self.serials:
            if bserial in self.serials_req:
                pass
            else:
                self.N_req += 1
                self.serials_req.append(bserial)
            motor_index = self.serials.index(bserial)
            with self.library.secure():
                state = self.library.get_present_state_dll(motor_index)
                log = logging.getLogger(__name__)
                msg = ('Motor %s position state is %s')
                log.info(msg,str(motor_index),str(state.CurPos))
            return motor_index
        else:
            mes = cleandoc('''The requested serial {} is absent from list {}'''
                   .format(serial, self.serials))
            raise InstrIOError(mes)

    def apply_standard_settings(self,motor_index):
        # To initialize one time when opening connection
        ## Mode
        with self.library.secure():
            mode = self.library.get_present_mode_dll(motor_index)
            mode.PMode = False;
            mode.PReg = True;
            mode.ResetD = False;
            mode.EMReset = False;
            mode.Tr1T = False;
            mode.Tr2T = False;
            mode.RotTrT = False;
            mode.Tr1En = False;
            mode.Tr2En = False;
            mode.RotTeEn = False;
            mode.Butt1T = False;
            mode.Butt2T = False;
            self.library.set_present_mode_dll(motor_index,mode)

        ## Parameters
        with self.library.secure():
            params = self.library.get_present_params_dll(motor_index)
            params.PTimeout = 10000000;
            params.MaxTemp = 65;
            self.library.set_present_params_dll(motor_index,params)

    def get_present_state(self,motor_index):
        with self.library.secure():
            return self.library.get_present_state_dll(motor_index)

    def get_present_params(self,motor_index):
        # To obtain present params (acc/deacc times(ms) & steps resol) on a motor
        with self.library.secure():
            return self.library.get_present_params_dll(motor_index)

    def set_params(self,motor_index,accel_time=None,decel_time=None,RT_delta=None):
        # Set the defined keywords as new params
        with self.library.secure():
            params = self.library.get_present_params_dll(motor_index)
            if accel_time is not None:
                params.AccelT = int(accel_time)
            if decel_time is not None:
                params.DecelT = int(decel_time)
            if RT_delta is not None:
                params.RTdelta = int(RT_delta)
            self.library.set_present_params_dll(motor_index,params)

    def turn_on_motor(self,motor_index):
        with self.library.secure():
            mode = self.library.get_present_mode_dll(motor_index)
            mode.resetD = False ## Bit if True, indicates to go to a full step pos and turn off power
            self.library.set_present_mode_dll(motor_index,mode)

    def turn_off_motor(self,motor_index):
        with self.library.secure():
            self.library.stop_motion_dll(motor_index)
            mode = self.library.get_present_mode_dll(motor_index)
            mode.resetD = True ## Bit if True, indicates to go to a full step pos and turn off power
            log = logging.getLogger(__name__)
            msg = ('Turning off motor with bit to %s')
            log.info(msg,str(mode.resetD))
            self.library.set_present_mode_dll(motor_index,mode)
            mode = self.library.get_present_mode_dll(motor_index)
            state = self.library.get_present_state_dll(motor_index)
            time.sleep(0.1)
            log = logging.getLogger(__name__)
            msg = ('Motor power is Power %s, ResetD %s')
            log.info(msg,str(state.Power),str(mode.ResetD))

    def move_motor(self,motor_index,destination,speed=4000.0):
        """
        Move motor to destination
        Destination in microsteps
        Speed in microsteps/s 
        """
        with self.library.secure():
            start_params = self.library.get_start_params_dll(motor_index)
            start_params.SDivisor = self.step_resolution
            destination_int = int(destination)
            speed_c = ctypes.c_float(speed)
            self.library.start_motion_dll(motor_index,destination_int,speed_c,start_params)

    def stop_motor(self,motor_index):
        # Stops motor immediately
        with self.library.secure():
            self.library.stop_motion_dll(motor_index)

    def release_motor(self,serial):
        # Take out motor of the list of used devices
        bserial = bytes(serial, 'ascii')
        if bserial in self.serials_req:
            self.serials_req.remove(bserial)
            self.N_req -= 1

    def _cleanup(self):
        # Make sure we disconnect all the motors and close the .exe at the end
        for i in range(self.N):
            self.turn_off_motor(i)
        with self.library.secure():
            self.library.close_dll()

    def close_library(self):
        with self.library.secure():
            self.library.close_dll()

####################################################
##### Instrument driver, quering to controller #####
####################################################

class USMC_Motor(DllInstrument):
    """Class for controlling single stepper motor. By
    default ``RotationalStage` is asssumed. This class initializes 
    a single instance of `USMCControlUnit` class.

    Attributes
    ----------
    parameters : USMC_Parameters
    mode : USMC_Mode
    state : USMC_State
    startParameters : USMC_StartParameters
    encoderState : USMC_EncoderState
    
    """

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(USMC_Motor, self).__init__(connection_info, caching_allowed,
                                      caching_permissions, auto_open)
        self._infos = connection_info
        self._id = self._infos['instr_id']
        self._cu = None
        self._motorindex = None

        if auto_open:
            self.open_connection()

    def open_connection(self):
        """Setup the right motor axis based on the serial id.

        """
        log = logging.getLogger(__name__)
        msg = ('Opening connection ...')
        log.info(msg)
        self._cu = USMC_Controller(self._infos)
        self._cu.open_library()
        self._motorindex = self._cu.request_motor(self._id)
        self._cu.apply_standard_settings(self._motorindex) #This also turns on motor by ResetD = 0
        self._cu.set_params(self._motorindex,accel_time=300,decel_time=300,RT_delta=8)

    def close_connection(self):
        """Close dll from the controller

        """
        log = logging.getLogger(__name__)
        msg = ('Closing connection ...')
        log.info(msg)
        self._cu.turn_off_motor(self._motorindex)
        self._cu.release_motor(self._id)
        self._cu.close_library()

    def move_motor_abs(self, angle_val):
        """Move motor by an angle to requested angle (rounded to 0.1deg)
        after previous step has finished,
        for consistency

        """
        round_angle = np.round(angle_val,1)
        new_pos = int(round_angle * 800)
        while self.is_moving():
           time.sleep(0.03)
        self._cu.move_motor(self._motorindex,new_pos)
        time.sleep(0.01)
        while self.is_moving():
            time.sleep(0.01)
        time.sleep(0.01)
        while self.is_moving(): #This helps getting the motion detection right, it needs two queries
            time.sleep(0.01)

    def move_motor_rel(self, angle_motion):
        """Move motor by an angle to requested angle (rounded to 0.1deg)
        after previous step has finished, 
        for consistency

        """
        round_angle = np.round(angle_motion,1)
        pres_angle =  np.round(self.get_present_abs_angle(),1)
        new_angle = pres_angle + round_angle
        new_pos = int(new_angle * 800)
        while self.is_moving():
            time.sleep(0.03)
        self._cu.move_motor(self._motorindex,new_pos)
        time.sleep(0.01)
        while self.is_moving():
            time.sleep(0.01)
        time.sleep(0.01)    
        while self.is_moving(): #This helps getting the motion detection right, it needs two queries
            time.sleep(0.01)

    def get_present_abs_angle(self):
        state = self._cu.get_present_state(self._motorindex)
        return state.CurPos/800

    def is_moving(self):
        state = self._cu.get_present_state(self._motorindex)
        log = logging.getLogger(__name__)
        msg = ('Rotate status: %s')
        log.info(msg,bool(state.RUN))
        return state.RUN
