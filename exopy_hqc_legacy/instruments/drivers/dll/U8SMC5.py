# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2023 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""
This driver uses a wrapper module to control Standa 8SMC5-USBhF stepper motor
controllers (https://www.standa.lt/products/catalog/motorised_positioners?item=525)
from Python. The module requires ximc developement package to be
installed and to point to its path in the connection info.
This file uses classes from PyXIMC that were edited by ExopyHqcLegacy Authors.
"""

import os
import sys
import platform
import importlib

import time
import atexit

import ctypes

import numpy as np
import logging #/!\

from contextlib import contextmanager
from threading import Lock

from inspect import cleandoc

from ..dll_tools import DllInstrument
from ..driver_tools import (InstrIOError, secure_communication,
                            instrument_property)
from . import pyximc as pyx

####################################
#### Using the provided wrapper ####
####################################

class USMC5_USB_Dll(object):
    """ Singleton class used to call the USMC dll.

    This class should wrap in python all useful call to the dll, so that the
    driver never need to access the _instance attribute. All manipulation of
    the dll should be done inside the secure context for thread safety. We use
    a provided wrapper to have all functions accessible.
    Dll files: bindy.dll, libximc.dll, xiwrapper.dll
    Wrapper: pyximc.py

    Parameters
    ----------

    infos : connection infos used to acces the wrapper (and dll)
        Timeout to use when attempting to acquire the library lock.

    This main class connects to USMCDLL.dll module and initializes the required 
    (= not all) motors.


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
        self = super(USMC5_USB_Dll, cls).__new__(cls)

        log = logging.getLogger(__name__)
        msg = ('Calling dll lib from 8SMC5-USB controller')
        log.info(msg)

        # Load library dll
        try: 
            if platform.system() == "Linux":
                self._dll = ctypes.CDLL(os.path.join(infos.get('lib_dir', ''),
                                        'libximc.so'))
            elif platform.system() == "FreeBSD":
                self._dll = ctypes.CDLL(os.path.join(infos.get('lib_dir', ''),
                                        'libximc.so'))
            elif platform.system() == "Darwin":
                self._dll = ctypes.CDLL(os.path.join(infos.get('lib_dir', ''),
                                        'libximc.framework/libximc'))
            elif platform.system() == "Windows":
                if sys.version_info[0] == 3 and sys.version_info[0] >= 8:
                    self._dll = ctypes.WinDLL(os.path.join(infos.get('lib_dir', ''),
                                        'libximc.dll'), winmode=ctypes.RTLD_GLOBAL)
                else:
                    self._dll = ctypes.WinDLL(os.path.join(infos.get('lib_dir', ''),
                                        'libximc.dll'))
            else:
                raise IOError(cleandoc("""Can't import pyximc module for this platform"""))
        except ImportError as err:
            raise InstrIOError(cleandoc("""Can't import pyximc module. The most probable reason is 
                that you the connection info do not point to the development pack.
                See developers' documentation for details."""))
        except OSError as err:
            log = logging.getLogger(__name__)
            msg = ('Err details are {},{},{},{}')
            log.info(msg,err.errno, err.filename, err.strerror, err.winerror) # Allows for displaying detailed information by mistake.
            if platform.system() == "Windows":
                if err.winerror == 193:  # The bit depth of one of the libraries bindy.dll, libximc.dll, xiwrapper.dll does not correspond to the operating system bit.
                    raise InstrIOError(cleandoc("""Err: The bit depth of one of the libraries 
                                                   bindy.dll, libximc.dll, xiwrapper.dll 
                                                   does not correspond to the operating system bit."""))
                elif err.winerror == 126: # One of the library bindy.dll, libximc.dll, xiwrapper.dll files is missing.
                    raise InstrIOError(cleandoc("""Err: One of the library bindy.dll, libximc.dll, xiwrapper.dll is missing.
                                                   It is also possible that one of the system libraries is missing. This problem 
                                                   is solved by installing the vcredist package from the ximc\\winXX folder."""))
                else:           # Other errors the value of which can be viewed in the code.
                    raise InstrIOError(cleandoc(str(err)))
            else:
                raise InstrIOError(cleandoc(str(err)+"""Can't load libximc library. Please add all shared libraries to the 
                                                        appropriate places. It is decribed in detail in developers' documentation. 
                                                        On Linux make sure you installed libximc-dev package. Make sure that the 
                                                        architecture of the system and the interpreter is the same"""))

        # Clarify function types
        self._dll.enumerate_devices.restype = ctypes.POINTER(pyx.device_enumeration_t)
        self._dll.get_device_name.restype = ctypes.c_char_p

        # Define lock for thread safety
        self.timeout = kwargs.get('timeout', 2.0)
        self.lock = Lock()

        # Initialize connected motors info
        with self.secure():
            self.initialize_motors_info_dll()

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

    def initialize_motors_info_dll(self):
        probe_flags = pyx.EnumerateFlags.ENUMERATE_PROBE + pyx.EnumerateFlags.ENUMERATE_NETWORK
        enum_hints = b"addr="
        dev_enum =  self._dll.enumerate_devices(probe_flags, enum_hints)
        dev_count = self._dll.get_device_count(dev_enum)
        enum_names = []
        controller_names = []
        serials = []
        controller_name = pyx.controller_name_t()
        enum_serial = ctypes.c_uint32()
        for dev_ind in range(dev_count):
            enum_name = self._dll.get_device_name(dev_enum, dev_ind)
            enum_names.append(enum_name)
            result_a = self._dll.get_enumerate_device_controller_name(dev_enum, dev_ind, ctypes.byref(controller_name))
            result_b = self._dll.get_enumerate_device_serial(dev_enum, dev_ind, ctypes.byref(enum_serial))
            if (result_a == pyx.Result.Ok) and (result_b == pyx.Result.Ok):
                controller_names.append(controller_name.ControllerName)
                serials.append(enum_serial)
                log = logging.getLogger(__name__)
                log.info("Enumerated device #{}. ".format(dev_ind) + 
                         "Name (port name): {} . ".format(str(enum_name, 'ascii')) + 
                         "Serial: {} . ".format(enum_serial.value) +
                         "Friendly name: {} . ".format(str(controller_name.ControllerName, 'ascii'))
                         )
        self._dev_count = dev_count
        self._enum_names = enum_names
        self._controller_names = controller_names
        self._serials = serials
        self._settings_done = [False]*dev_count
        self._dll.free_enumerate_devices(dev_enum)

    def get_ximc_version_dll(self):
        sbuf = ctypes.create_string_buffer(64)
        self._dll.ximc_version(sbuf)
        return sbuf.raw.decode().rstrip("\0")

    def get_connected_devices_dll(self):
        return self._dev_count, self._serials

    def open_device_dll(self,serial):
        for dev_ind in range(self._dev_count):
            if (self._serials[dev_ind].value == serial):
                motor_index = self._dll.open_device(self._enum_names[dev_ind])
                return motor_index
        raise InstrIOError('Serial number of motor to open by XIMC not found')

    def get_motor_fridenly_name_dll(self,motor_index):
        controller_name = pyx.controller_name_t()
        result_a = self._dll.get_controller_name(motor_index, ctypes.byref(controller_name))
        if (result_a == pyx.Result.Ok):
            return str(controller_name.ControllerName, 'ascii')

    def get_settings_done_dll(self,serial):
        for dev_ind in range(self._dev_count):
            if (self._serials[dev_ind].value == serial):
                return self._settings_done[dev_ind]
        raise InstrIOError('Serial number of motor to get settings done by XIMC not found')

    def set_settings_done_dll(self,serial):
        for dev_ind in range(self._dev_count):
            if (self._serials[dev_ind].value == serial):
                self._settings_done[dev_ind] = True
                return None
        raise InstrIOError('Serial number of motor to set settings done by XIMC not found')

    def apply_standard_settings_dll(self,dev_string,motor_index):
        if dev_string == '8MRU-1TP':
            return pyx.set_profile_8MRU_1TP(self._dll, motor_index)
        else:
            raise NotImplementedError('Unknown motor name')

    def apply_engine_settings_dll(self,motor_index,NomVoltage,NomCurrent,NomSpeed,uNomSpeed,EngineFlags,Antiplay,MicrostepMode,StepsPerRev):
        engine_settings = pyx.engine_settings_t()
        engine_settings.NomVoltage = NomVoltage
        engine_settings.NomCurrent = NomCurrent
        engine_settings.NomSpeed = NomSpeed
        engine_settings.uNomSpeed = uNomSpeed
        engine_settings.EngineFlags = EngineFlags
        engine_settings.Antiplay = Antiplay
        engine_settings.MicrostepMode = MicrostepMode
        engine_settings.StepsPerRev = StepsPerRev
        return self._dll.set_engine_settings(motor_index, ctypes.byref(engine_settings))

    def apply_move_settings_dll(self,motor_index,Speed,uSpeed,Accel,Decel,AntiplaySpeed,uAntiplaySpeed):
        move_settings = pyx.move_settings_t()
        move_settings.Speed = Speed
        move_settings.uSpeed = uSpeed
        move_settings.Accel = Accel
        move_settings.Decel = Decel
        move_settings.AntiplaySpeed = AntiplaySpeed
        move_settings.uAntiplaySpeed = uAntiplaySpeed
        return self._dll.set_move_settings(motor_index, ctypes.byref(move_settings))

    def apply_home_settings_dll(self,motor_index,FastHome,uFastHome,SlowHome,uSlowHome,HomeDelta,uHomeDelta,HomeFlags):
        home_settings = pyx.home_settings_t()
        home_settings.FastHome = FastHome
        home_settings.uFastHome = uFastHome
        home_settings.SlowHome = SlowHome
        home_settings.uSlowHome = uSlowHome
        home_settings.HomeDelta = HomeDelta
        home_settings.uHomeDelta = uHomeDelta
        home_settings.HomeFlags = HomeFlags
        return self._dll.set_home_settings(motor_index, ctypes.byref(home_settings))

    def apply_noemf_settings_dll(self,motor_index):
        emf_settings = pyx.emf_settings_t()
        emf_settings.L = 0
        emf_settings.R = 0
        emf_settings.Km = 0
        emf_settings.BackEMFFlags = 0
        return self._dll.set_emf_settings(motor_index, ctypes.byref(emf_settings))

    def apply_power_settings_dll(self,motor_index,HoldCurrent,CurrReductDelay,PowerOffDelay,CurrentSetTime,PowerFlags):
        power_settings = pyx.power_settings_t()
        power_settings.HoldCurrent = HoldCurrent
        power_settings.CurrReductDelay = CurrReductDelay
        power_settings.PowerOffDelay = PowerOffDelay
        power_settings.CurrentSetTime = CurrentSetTime
        power_settings.PowerFlags = PowerFlags
        return self._dll.set_power_settings(motor_index, ctypes.byref(power_settings))

    def apply_brake_settings_dll(self,motor_index,t1,t2,t3,t4,BrakeFlags):
        brake_settings = pyx.brake_settings_t()
        brake_settings.t1 = t1
        brake_settings.t2 = t2
        brake_settings.t3 = t3
        brake_settings.t4 = t4
        brake_settings.BrakeFlags = BrakeFlags
        return self._dll.set_brake_settings(motor_index, ctypes.byref(brake_settings))

    def apply_control_settings_dll(self,motor_index,MaxSpeed,uMaxSpeed,Timeout,MaxClickTime,Flags,DeltaPosition,uDeltaPosition):
        control_settings = pyx.control_settings_t()
        for i in range(len(MaxSpeed)):
            control_settings.MaxSpeed[i] = MaxSpeed[i]
        for i in range(len(MaxSpeed),10):
            control_settings.MaxSpeed[i] = 0
        for i in range(len(uMaxSpeed)):
            control_settings.uMaxSpeed[i] = uMaxSpeed[i]
        for i in range(len(uMaxSpeed),10):
            control_settings.uMaxSpeed[i] = 0
        for i in range(len(Timeout)):
            control_settings.Timeout[i] = Timeout[i]
        for i in range(len(Timeout),9):
            control_settings.Timeout[i] = 1000
        control_settings.MaxClickTime = MaxClickTime
        control_settings.Flags = Flags
        control_settings.DeltaPosition = DeltaPosition
        control_settings.uDeltaPosition = uDeltaPosition
        return self._dll.set_control_settings(motor_index, ctypes.byref(control_settings))

    def get_status_dll(self,motor_index):
        x_status = pyx.status_t()
        result = self._dll.get_status(motor_index, ctypes.byref(x_status))
        if (result != pyx.Result.Ok):
            raise InstrIOError('Could not get motor status')
        return x_status.MoveSts,x_status.CurSpeed,x_status.Flags

    def get_position_dll(self,motor_index):
        x_pos = pyx.get_position_t()
        result = self._dll.get_position(motor_index, ctypes.byref(x_pos))
        if (result != pyx.Result.Ok):
            raise InstrIOError('Could not read motor position')
        return x_pos.Position, x_pos.uPosition

    def set_position_dll(self,motor_index,Position,uPosition):
        result = self._dll.command_move(motor_index, Position, uPosition)
        if (result != pyx.Result.Ok):
            raise InstrIOError('Could not start motor motion')

    def set_position_rel_dll(self,motor_index,rPosition,ruPosition):
        result = self._dll.command_movr(motor_index, rPosition, ruPosition)
        if (result != pyx.Result.Ok):
            raise InstrIOError('Could not start motor relative motion')

    def stop_motion_dll(self,motor_index):
        result = self._dll.command_sstp(motor_index)
        if (result != pyx.Result.Ok):
            raise InstrIOError('Could not stop motor')

    def close_device_dll(self,motor_index):
        self._dll.close_device(ctypes.byref(ctypes.cast(motor_index, ctypes.POINTER(ctypes.c_int))))

    def close_library_dll(self):
        OS = platform.system()

        if OS == "Windows":
            dll_close = ctypes.windll.kernel32.FreeLibrary
        elif OS == "Linux":
            try:
                stdlib = ctypes.CDLL("")
            except OSError:
                # Alpine Linux.
                stdlib = ctypes.CDLL("libc.so")
            dll_close = stdlib.dlclose
        elif sys.platform == "cygwin":
            stdlib = ctypes.CDLL("cygwin1.dll")
            dll_close = stdlib.dlclose
        elif OS == "FreeBSD":
            # FreeBSD uses `/usr/lib/libc.so.7` where `7` is another version number.
            # It is not in PATH but using its name instead of its path is somehow the
            # only way to open it. The name must include the .so.7 suffix.
            stdlib = ctypes.CDLL("libc.so.7")
            dll_close = stdlib.close
        else:
            raise NotImplementedError('Unknown platform.')

        dll_close.argtypes = [ctypes.c_void_p]
        dll_close(self._dll._handle)

###########################################
##### Controller interacting with DLL #####
###########################################

class USMC5_Controller(object):
    """
    Class for controlling all motors. By default a 1 axis stage 
    is asssumed. This class initializes a single instance of the 
    `dll` class at any time when executing open_library.
    """

    def __init__(self, connection_infos):
        super(USMC5_Controller, self).__init__()
        self.infos = connection_infos
        atexit.register(self.close_library)

    def open_library(self):
        self.library = USMC5_USB_Dll(self.infos)
        with self.library.secure():
            self.ximc_version = self.library.get_ximc_version_dll()

        # Version check
        log = logging.getLogger(__name__)
        msg = ('XIMC version loaded is %s')
        log.info(msg,self.ximc_version)
        if self.ximc_version != pyx.VERSION :
            raise InstrIOError(cleandoc("""The loaded XIMC at path specified in connection_infos is {}
                                           and does not match with the version required here by exopy, {}""".format(
                                           self.ximc_version,pyx.VERSION)))

        # Devices search
        with self.library.secure():
            self.N, self.culong_serials = self.library.get_connected_devices_dll()

        # Controller list preparation
        self.serials = [culong_serial.value for culong_serial in self.culong_serials]
        self.N_req = 0
        self.serials_req = []
        self.device_ids = [pyx.device_t]*self.N
        log = logging.getLogger(__name__)
        msg = ('Motors found are %s in total, with serials %s')
        log.info(msg,str(self.N),';'.join([str(serial) for serial in self.serials]))

    def get_motors_serials(self):
        return self.serials

    def request_motor(self,serial):
        # Add motor defined by its int serial to list of used devices 
        # and returns its device identifier for easy adressing
        if serial in self.serials:
            N_in_serials = self.serials.index(serial)
            if serial in self.serials_req:
                pass
            else:
                with self.library.secure():
                    motor_identifier = self.library.open_device_dll(serial)
                self.N_req += 1
                self.serials_req.append(serial)
                self.device_ids[N_in_serials] = motor_identifier
                log = logging.getLogger(__name__)
                log.info("Opened Device #{}, id: {} ".format(N_in_serials, repr(motor_identifier)))
            return self.device_ids[N_in_serials]
        else:
            raise InstrIOError(cleandoc("""The motor with requested serial {}
                                           is not seen by the controller""".format(
                                           serial)))

    def get_settings_done(self,serial):
        with self.library.secure():
            return self.library.get_settings_done_dll(serial)

    def set_settings_done(self,serial):
        with self.library.secure():
            self.library.set_settings_done_dll(serial)

    def apply_standard_settings(self,dev_string,motor_index):
        # To initialize one time when opening connection
        with self.library.secure():
            motor_name = self.library.get_motor_fridenly_name_dll(motor_index)
        if motor_name == dev_string:
            with self.library.secure():
                return_value = self.library.apply_standard_settings_dll(dev_string,motor_index)
            if return_value == pyx.Result.Ok:
                log = logging.getLogger(__name__)
                log.info("Loaded standard settings for device id{}, using profile: {}".format(motor_index, dev_string))
            else:
                raise InstrIOError(cleandoc("""Failed in applying standard settings for device id{}, 
                                               with profile: {} """.format(motor_index, dev_string)))
        else:
            raise InstrIOError(cleandoc("""Trying to apply standard settings of {}
                                      to motor a with name {}""".format(dev_string,motor_name)))

    def apply_engine_settings(self,motor_index,NomVoltage,NomCurrent,NomSpeed,uNomSpeed,EngineFlag,Antiplay,MicrostepMode,StepsPerRev):
        with self.library.secure():
            return_value = self.library.apply_engine_settings_dll(motor_index,NomVoltage,NomCurrent,NomSpeed,uNomSpeed,EngineFlag,Antiplay,MicrostepMode,StepsPerRev)
        if return_value != pyx.Result.Ok:
            raise InstrIOError(cleandoc("Failed in applying engine settings for device id{}".format(motor_index)))

    def apply_move_settings(self,motor_index,Speed,uSpeed,Accel,Decel,AntiplaySpeed,uAntiplaySpeed):
        with self.library.secure():
            return_value = self.library.apply_move_settings_dll(motor_index,Speed,uSpeed,Accel,Decel,AntiplaySpeed,uAntiplaySpeed)
        if return_value != pyx.Result.Ok:
            raise InstrIOError(cleandoc("Failed in applying move settings for device id{}".format(motor_index)))

    def apply_home_settings(self,motor_index,FastHome,uFastHome,SlowHome,uSlowHome,HomeDelta,uHomeDelta,HomeFlags):
        with self.library.secure():
            return_value = self.library.apply_home_settings_dll(motor_index,FastHome,uFastHome,SlowHome,uSlowHome,HomeDelta,uHomeDelta,HomeFlags)
        if return_value != pyx.Result.Ok:
            raise InstrIOError(cleandoc("Failed in applying home settings for device id{}".format(motor_index)))

    def apply_noemf_settings(self,motor_index):
        with self.library.secure():
            return_value = self.library.apply_noemf_settings_dll(motor_index)
        if return_value != pyx.Result.Ok:
            raise InstrIOError(cleandoc("Failed in applying emf settings for device id{}".format(motor_index)))
    
    def apply_power_settings(self,motor_index,HoldCurrent,CurrReductDelay,PowerOffDelay,CurrentSetTime,PowerFlags):
        with self.library.secure():
            return_value = self.library.apply_power_settings_dll(motor_index,HoldCurrent,CurrReductDelay,PowerOffDelay,CurrentSetTime,PowerFlags)
        if return_value != pyx.Result.Ok:
            raise InstrIOError(cleandoc("Failed in applying power settings for device id{}".format(motor_index)))

    def apply_brake_settings(self,motor_index,t1,t2,t3,t4,BrakeFlags):
        with self.library.secure():
            return_value = self.library.apply_brake_settings_dll(motor_index,t1,t2,t3,t4,BrakeFlags)
        if return_value != pyx.Result.Ok:
            raise InstrIOError(cleandoc("Failed in applying brake settings for device id{}".format(motor_index)))

    def apply_control_settings(self,motor_index,MaxSpeed,uMaxSpeed,Timeout,MaxClickTime,Flags,DeltaPosition,uDeltaPosition):
        with self.library.secure():
            return_value = self.library.apply_control_settings_dll(motor_index,MaxSpeed,uMaxSpeed,Timeout,MaxClickTime,Flags,DeltaPosition,uDeltaPosition)
        if return_value != pyx.Result.Ok:
            raise InstrIOError(cleandoc("Failed in applying control settings for device id{}".format(motor_index)))

    def get_present_status(self,motor_index):
        with self.library.secure():
            moveSts,curSpeed,flags = self.library.get_status_dll(motor_index)
        flags_strs=[]
        if ((flags & pyx.StateFlags.STATE_ERRC) == pyx.StateFlags.STATE_ERRC):
            flags_strs.append('Command error encountered.')
        if ((flags & pyx.StateFlags.STATE_ERRD) == pyx.StateFlags.STATE_ERRD):
            flags_strs.append('Data integrity error encountered.')
        if ((flags & pyx.StateFlags.STATE_ERRV) == pyx.StateFlags.STATE_ERRV):
            flags_strs.append('Value error encountered.')
        if ((flags & pyx.StateFlags.STATE_EEPROM_CONNECTED) == pyx.StateFlags.STATE_EEPROM_CONNECTED):
            flags_strs.append('EEPROM with settings is connected.')
        if ((flags & pyx.StateFlags.STATE_IS_HOMED) == pyx.StateFlags.STATE_IS_HOMED):
            flags_strs.append('Calibration and homing performed.')
        if ((flags & pyx.StateFlags.STATE_ALARM) == pyx.StateFlags.STATE_ALARM):
            flags_strs.append('Controller is in alarm pyx.STATE indicating that something dangerous had happened.')
        if ((flags & pyx.StateFlags.STATE_CTP_ERROR) == pyx.StateFlags.STATE_CTP_ERROR):
            flags_strs.append('Control position error(is only used with stepper motor).')
        if ((flags & pyx.StateFlags.STATE_SECUR) == pyx.StateFlags.STATE_SECUR):
            flags_strs.append('On top of other errors above, there are remaining ones in flag {}.'.format(flags & pyx.StateFlags.STATE_SECUR))
        return moveSts,curSpeed,flags_strs

    def get_position(self,motor_index):
        with self.library.secure():
            current_position_step, current_position_ustep = self.library.get_position_dll(motor_index)
        return current_position_step, current_position_ustep

    def move_motor(self,motor_index,Position,uPosition):
        with self.library.secure():
            self.library.set_position_dll(motor_index,Position,uPosition)

    def move_motor_rel(self,motor_index,rPosition,ruPosition):
        with self.library.secure():
            self.library.set_position_rel_dll(motor_index,rPosition,ruPosition)

    def stop_motor(self,motor_index):
        with self.library.secure():
            self.library.stop_motion_dll(motor_index)

    def release_motor(self,serial,motor_index):
        # Take out motor of the list of used devices
        if serial in self.serials_req:
            self.stop_motor(motor_index)
            with self.library.secure():
                self.library.close_device_dll(motor_index)
            self.serials_req.remove(serial)
            self.N_req -= 1

    def close_library(self):
        for serial in self.serials_req:
            N_in_serials = self.serials.index(serial)
            self.release_motor(serial,self.device_ids[N_in_serials])
        with self.library.secure():
            self.library.close_library_dll()

####################################################
##### Instrument driver, quering to controller #####
####################################################

class U8SMC5_8MRU_1TP_Motor(DllInstrument):
    """Class for controlling single stepper motor.

    Attributes
    ----------

    
    """

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(U8SMC5_8MRU_1TP_Motor, self).__init__(connection_info, caching_allowed,
                                      caching_permissions, auto_open)
        self._infos = connection_info
        self._id = int(self._infos['instr_id'])
        self._cu = None
        self._motorindex = None
        self._motorsteps = None
        self._motorusteps = None
        self._motion_timeout = 5.0
        if auto_open:
            self.open_connection()

    def open_connection(self):
        """Setup the right motor axis based on the serial id.

        """
        log = logging.getLogger(__name__)
        msg = ('Opening connection to 8MRU_1TP motor with dll')
        log.info(msg)
        self._cu = USMC5_Controller(self._infos)
        self._cu.open_library()
        #The following line returns the index used in dll calls to address this particular motor
        self._motorindex = self._cu.request_motor(self._id)
        #The standard parameters for the present motor type are to be applied only
        #at first open for this instrument defined by its serial id
        if not(self._cu.get_settings_done(self._id)):
            #The following line applies a standard python language profile provided by Standa and 
            #amended and appended to our pyximc.py
            self._cu.apply_standard_settings('8MRU-1TP',self._motorindex)
            #The following lines apply further fine tuning of these parameters
            self._cu.apply_engine_settings(self._motorindex,360,1000,10,0,144,1800,9,200)
            self._cu.apply_move_settings(self._motorindex,10,0,10,10,2000,0)
            self._cu.apply_home_settings(self._motorindex,100,0,50,0,-9,0,370)
            self._cu.apply_noemf_settings(self._motorindex)
            self._cu.apply_power_settings(self._motorindex,50,1000,60,300,4)
            self._cu.apply_brake_settings(self._motorindex,300,500,300,400,1)
            self._cu.apply_control_settings(self._motorindex,[60,600],[],[],300,2,1,0)
            self._cu.set_settings_done(self._id)
        #According to parameters passed above, we have
        self._motorsteps = 200
        self._motorusteps = 256
        self._speed = 10

    def close_connection(self):
        """Close dll from the controller

        """
        log = logging.getLogger(__name__)
        msg = ('Closing connection to 8MRU_1TP motor with dll')
        log.info(msg)
        self._cu.release_motor(self._id,self._motorindex)

    def move_motor_abs(self, angle_val):
        """Move motor by an angle to requested angle (rounded to 0.1deg)
        after previous step has finished,
        for consistency

        """
        #Waits first for previous motion completion
        t = 0
        while self.is_moving():
            time.sleep(0.03)
            t += 0.03
            if t > self._motion_timeout:
                raise InstrIOError('Timeout in waiting for motor to stop from previous motion')

        #Checks angles and position      
        start_angle = self.get_present_abs_angle()
        desired_motion_steps = np.abs(angle_val-start_angle)/360*self._motorsteps
        start_position_step, start_position_ustep = self._cu.get_position(self._motorindex)
        new_step  = int(np.fix(self._motorsteps*angle_val/360.0))
        new_ustep = int(np.round((self._motorsteps*angle_val/360.0-new_step)*self._motorusteps))

        if (np.abs(new_step-start_position_step)>0) or (np.abs(new_ustep-start_position_ustep)>0):
            #Then motion is required
            self._cu.move_motor(self._motorindex,new_step,new_ustep)
            time.sleep(0.03)
            
            #Waits for motion start
            t = 0
            while np.abs(start_angle-self.get_present_abs_angle())<180.0/(self._motorsteps*self._motorusteps):
                time.sleep(0.01)
                t += 0.01
                if t > self._motion_timeout:
                    raise InstrIOError('Timeout in waiting for motor to start')

            self.is_moving(log_status=True) #Get log
            time.sleep(0.01)

            #Waits for motion end
            t = 0
            while self.is_moving(): 
                time.sleep(0.01)
                t += 0.01
                if t > self._motion_timeout + desired_motion_steps/self._speed:
                    raise InstrIOError('Timeout in waiting for motor to arrive destination')

        self.is_moving(log_status=True) #Get final log

    def move_motor_rel(self, angle_motion):
        """Move motor by an angle to requested angle (rounded to 0.1deg)
        after previous step has finished, 
        for consistency

        """
        #Waits first for previous motion completion
        t = 0
        while self.is_moving():
            time.sleep(0.03)
            t += 0.03
            if t > self._motion_timeout:
                raise InstrIOError('Timeout in waiting for motor to stop from previous motion')

        #Checks angles and position      
        start_angle = self.get_present_abs_angle()
        desired_motion_steps = np.abs(angle_motion)/360*self._motorsteps
        new_rstep  = int(np.fix(self._motorsteps*angle_motion/360.0))
        new_rustep = int(np.round((self._motorsteps*angle_motion/360.0-new_rstep)*self._motorusteps))

        if (np.abs(new_rstep)>0) or (np.abs(new_rustep)>0):
            #Then motion is required
            self._cu.move_motor_rel(self._motorindex,new_rstep,new_rustep)
            time.sleep(0.03)

            #Waits for motion start
            t = 0
            while np.abs(start_angle-self.get_present_abs_angle())<180.0/(self._motorsteps*self._motorusteps):
                time.sleep(0.01)
                t += 0.01
                if t > self._motion_timeout:
                    raise InstrIOError('Timeout in waiting for motor to start')

            self.is_moving(log_status=True) #Get log
            time.sleep(0.01)

            #Waits for motion end
            t = 0
            while self.is_moving(): 
                time.sleep(0.01)
                t += 0.01
                if t > self._motion_timeout + desired_motion_steps/self._speed:
                    raise InstrIOError('Timeout in waiting for motor to arrive destination')

        self.is_moving(log_status=True) #Get final log

    def get_present_abs_angle(self):
        current_position_step, current_position_ustep = self._cu.get_position(self._motorindex)
        return np.round(360.0*(current_position_step/self._motorsteps + current_position_ustep/(self._motorsteps*self._motorusteps)),9)

    def is_moving(self,log_status=False):
        moveSts,curSpeed,flags_strs = self._cu.get_present_status(self._motorindex)
        res_moving = (bool(moveSts) or bool(curSpeed))
        if log_status:
            log = logging.getLogger(__name__)
            msg = ('Rotate status: %s at speed %s')
            log.info(msg,str(moveSts),str(curSpeed))
            for flag_str in flags_strs:
                log.info('8MRU_1TP motor flags: '+flag_str)
        return res_moving
