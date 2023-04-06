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
import time
import atexit
import ctypes
import numpy as np
import logging #/!\
import pyclibrary

from contextlib import contextmanager
from threading import Lock

from inspect import cleandoc

from ..dll_tools import DllInstrument
from ..driver_tools import (InstrIOError, secure_communication,
                            instrument_property)

class USMC_Dll(object):
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
        self = super(USMC_Dll, cls).__new__(cls)

        try:
            if sys.platform == 'win32':
                call("TASKKILL /F /IM MicroSMC.exe", shell=True)
        except Exception:
            pass

        cache_path = os.path.join(os.path.dirname(__file__),
                                      '8SMC1.pycctypes.libc')
        library_dir = os.path.join(infos.get('lib_dir', ''),
                                   'USMCDLL.dll')
        header_dir = os.path.join(infos.get('header_dir', ''),
                                  'USMCDLL.h')
        windefs = pyclibrary.win_defs()

#        log = logging.getLogger(__name__)
#        msg = ('Allowed wintypes are {}')
#        log.info(msg,print(windefs))

        def replace_WORD(matchobject):
            return matchobject.group(0)[:-4]+"UINT16"        

        headers = pyclibrary.CParser([header_dir], copy_from=windefs, replace={
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

        self._dll = pyclibrary.CLibrary(library_dir, headers, cache=cache_path,
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
            raise InstrIOError(cleandoc('Controller returned  {} at connection'
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
        self._dll.USMC_Close()

class USMC_Controller(object):
    """
    Class for controlling all motors. By
    default ``RotationalStage` is asssumed. This class initializes 
    a single instance of the `dll` class.
    """


    _instance = None

    def __new__(cls, infos):
        if cls._instance is not None:
            return cls._instance

        self = super(USMC_Controller, cls).__new__(cls)
        self.library = USMC_Dll(infos)
        with self.library.secure():
            self.N, self.serials = self.library.get_connected_devices_dll()
        self.N_req = 0
        self.serials_req = []

        log = logging.getLogger(__name__)
        msg = ('Motors found are %s in total, %s')
        log.info(msg,str(self.N),';'.join([str(bserial, 'ascii') for bserial in self.serials]))

        self.step_resolution = 8 #Now used as a global param of all motors for simplicity

        atexit.register(self._cleanup)
        cls._instance = self
        return self

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
            mode.PMode = 0;
            mode.PReg = 1;
            mode.ResetD = 0;
            mode.EMReset = 0;
            mode.Tr1T = 0;
            mode.Tr2T = 0;
            mode.RotTrT = 0;
            mode.Tr1En = 0;
            mode.Tr2En = 0;
            mode.RotTeEn = 0;
            mode.Butt1T = 0;
            mode.Butt2T = 0;
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
            mode.resetD = 0 ## Bit if True, indicates to go to a full step pos and turn off power
            self.library.set_present_mode_dll(motor_index,mode)

    def turn_off_motor(self,motor_index):
        with self.library.secure():
            mode = self.library.get_present_mode_dll(motor_index)
            mode.resetD = 1 ## Bit if True, indicates to go to a full step pos and turn off power
            self.library.set_present_mode_dll(motor_index,mode)

    def move_motor(self,motor_index,destination,speed=4000):
        """
        Move motor to destination
        Destination in microsteps
        Speed in microsteps/s 
        """
        with self.library.secure():
            startp = self.library.get_start_params_dll(motor_index)
            startp.SDivisor = self.step_resolution
            destination_int = int(destination)
            speed_c = ctypes.c_float
            speed_c = float(speed)
            speed_c_ptr = ctypes.cast(speed_c, ctypes.POINTER(ctypes.c_float))
            self.library.start_motion_dll(motor_index,destination_int,speed_c_ptr,startp)

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
        # Make sure we disconnect all the motors and close the .exe
        for i in range(self.N):
            self.turn_off_motor(i)
        with self.library.secure():
            self.library.close_dll()

    def close_controller(self):
        with self.library.secure():
            self.library.close_dll()

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
        self._cu = USMC_Controller(self._infos)
        self._motorindex = self._cu.request_motor(self._id)
        self._cu.apply_standard_settings(self._motorindex) #This also turns on motor by ResetD = 0
        self._cu.set_params(self._motorindex,accel_time=300,decel_time=300,RT_delta=8)

    def close_connection(self):
        """Do not explicitly close the .exe as it may re-arrange all.

        """
        self._cu.turn_off_motor(self._motorindex)
        self._cu.release_motor(self._id)
        self._cu.close_controller()

    def move_motor_abs(self, angle_val):
        """Move motor by an angle to requested angle (rounded to 0.1deg)
        after previous step has finished,
        for consistency

        """
        round_angle = np.round(angle_val,1)
        new_pos = int(round_angle * 800)
#        while self.is_moving():
#            sleep(0.05)
#        self._cu.move_motor(self._motorindex,new_pos)
#        while self.is_moving():
#            sleep(0.01)

    def move_motor_rel(self, angle_motion):
        """Move motor by an angle to requested angle (rounded to 0.1deg)
        after previous step has finished, 
        for consistency

        """
        round_angle = np.round(angle_motion,1)
        pres_angle =  np.round(self.get_present_abs_angle(),1)
        new_angle = pres_angle + round_angle
        new_pos = int(new_angle * 800)
#        while self.is_moving():
#            sleep(0.05)
#        self._cu.move_motor(self._motorindex,new_pos)
#        while self.is_moving():
#            sleep(0.01)

    def get_present_abs_angle(self):
        state = self._cu.get_present_state(self._motorindex)
        return state.CurPos/800

    def is_moving(self):
        state = self._cu.get_present_state(self._motorindex)
        return state.RUN
