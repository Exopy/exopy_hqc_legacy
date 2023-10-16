# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file comes PyXIMC and was edited by ExopyHqcLegacy Authors
# see AUTHORS for more details.
#
# -----------------------------------------------------------------------------
"""Python interface to the pyximc for 8SMC5-USB and profiles.

This module provides a thin wrapper on top of the XIMC API. 
All the exported methods directly map to underlying dll functions. 
Please see the XIMC documentation for detailed specification of
the functions. This module provides all classes for convenience.

Original files:
- pyximc.py
- 8MRU-1TP.py

Replacements in pyximc.py, to be done again if version upgrade is required:
- use of ctype not in main namespace bu with import ctypes to avoid conflicts
- added VERSION string used for consistency check with dll files version
- removed ximc_shared_lib loader of Dll to keep connection with explicit dll path (multi-version support)
- removed function type clarification (done in main dll driver class)
- add def for device_t

Replacements in 8MRU-1TP.py, to be done again if version upgrade is required:
- use of ctype not in main namespace but with import ctypes to avoidconflicts
- comment out set_controller_name to avoid overwriting the controller name '8MRU-1TP' get from flash
"""

import ctypes
import os
import platform
import sys

VERSION = "2.14.14"

# Equivalent of ximc-2.14.14\ximc\crossplatform\wrappers\python\pyximc.py
# This code is derived from the classes provided in pyximc.
# Only added class is device_t
# If updated, remember to update version number above.

class Result:
    Ok = 0
    Error = -1
    NotImplemented = -2
    ValueError = -3
    NoDevice = -4


class calibration_t(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('A', ctypes.c_double),
        ('MicrostepMode', ctypes.c_uint)
    ]

class device_t(ctypes.c_int):
    pass

class device_enumeration_t(ctypes.LittleEndianStructure):
    pass

class device_network_information_t(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('ipv4', ctypes.c_uint32),
        ('nodename', ctypes.c_char * 16),
        ('axis_state', ctypes.c_uint),
        ('locker_username', ctypes.c_char * 16),
        ('locker_nodename', ctypes.c_char * 16),
        ('locked_time', ctypes.c_ulonglong),
    ]


# ---------------------------
# BEGIN OF GENERATED code
# ---------------------------
class EnumerateFlags:
	ENUMERATE_PROBE      = 0x01
	ENUMERATE_ALL_COM    = 0x02
	ENUMERATE_NETWORK    = 0x04

class MoveState:
	MOVE_STATE_MOVING          = 0x01
	MOVE_STATE_TARGET_SPEED    = 0x02
	MOVE_STATE_ANTIPLAY        = 0x04

class ControllerFlags:
	EEPROM_PRECEDENCE    = 0x01

class PowerState:
	PWR_STATE_UNKNOWN    = 0x00
	PWR_STATE_OFF        = 0x01
	PWR_STATE_NORM       = 0x03
	PWR_STATE_REDUCT     = 0x04
	PWR_STATE_MAX        = 0x05

class StateFlags:
	STATE_CONTR                     = 0x000003F
	STATE_ERRC                      = 0x0000001
	STATE_ERRD                      = 0x0000002
	STATE_ERRV                      = 0x0000004
	STATE_EEPROM_CONNECTED          = 0x0000010
	STATE_IS_HOMED                  = 0x0000020
	STATE_SECUR                     = 0x1B3FFC0
	STATE_ALARM                     = 0x0000040
	STATE_CTP_ERROR                 = 0x0000080
	STATE_POWER_OVERHEAT            = 0x0000100
	STATE_CONTROLLER_OVERHEAT       = 0x0000200
	STATE_OVERLOAD_POWER_VOLTAGE    = 0x0000400
	STATE_OVERLOAD_POWER_CURRENT    = 0x0000800
	STATE_OVERLOAD_USB_VOLTAGE      = 0x0001000
	STATE_LOW_USB_VOLTAGE           = 0x0002000
	STATE_OVERLOAD_USB_CURRENT      = 0x0004000
	STATE_BORDERS_SWAP_MISSET       = 0x0008000
	STATE_LOW_POWER_VOLTAGE         = 0x0010000
	STATE_H_BRIDGE_FAULT            = 0x0020000
	STATE_WINDING_RES_MISMATCH      = 0x0100000
	STATE_ENCODER_FAULT             = 0x0200000
	STATE_ENGINE_RESPONSE_ERROR     = 0x0800000
	STATE_EXTIO_ALARM               = 0x1000000

class GPIOFlags:
	STATE_DIG_SIGNAL      = 0xFFFF
	STATE_RIGHT_EDGE      = 0x0001
	STATE_LEFT_EDGE       = 0x0002
	STATE_BUTTON_RIGHT    = 0x0004
	STATE_BUTTON_LEFT     = 0x0008
	STATE_GPIO_PINOUT     = 0x0010
	STATE_GPIO_LEVEL      = 0x0020
	STATE_BRAKE           = 0x0200
	STATE_REV_SENSOR      = 0x0400
	STATE_SYNC_INPUT      = 0x0800
	STATE_SYNC_OUTPUT     = 0x1000
	STATE_ENC_A           = 0x2000
	STATE_ENC_B           = 0x4000

class EncodeStatus:
	ENC_STATE_ABSENT     = 0x00
	ENC_STATE_UNKNOWN    = 0x01
	ENC_STATE_MALFUNC    = 0x02
	ENC_STATE_REVERS     = 0x03
	ENC_STATE_OK         = 0x04

class WindStatus:
	WIND_A_STATE_ABSENT     = 0x00
	WIND_A_STATE_UNKNOWN    = 0x01
	WIND_A_STATE_MALFUNC    = 0x02
	WIND_A_STATE_OK         = 0x03
	WIND_B_STATE_ABSENT     = 0x00
	WIND_B_STATE_UNKNOWN    = 0x10
	WIND_B_STATE_MALFUNC    = 0x20
	WIND_B_STATE_OK         = 0x30

class MvcmdStatus:
	MVCMD_NAME_BITS    = 0x3F
	MVCMD_UKNWN        = 0x00
	MVCMD_MOVE         = 0x01
	MVCMD_MOVR         = 0x02
	MVCMD_LEFT         = 0x03
	MVCMD_RIGHT        = 0x04
	MVCMD_STOP         = 0x05
	MVCMD_HOME         = 0x06
	MVCMD_LOFT         = 0x07
	MVCMD_SSTP         = 0x08
	MVCMD_ERROR        = 0x40
	MVCMD_RUNNING      = 0x80

class MoveFlags:
	RPM_DIV_1000    = 0x01

class EngineFlags:
	ENGINE_REVERSE           = 0x01
	ENGINE_CURRENT_AS_RMS    = 0x02
	ENGINE_MAX_SPEED         = 0x04
	ENGINE_ANTIPLAY          = 0x08
	ENGINE_ACCEL_ON          = 0x10
	ENGINE_LIMIT_VOLT        = 0x20
	ENGINE_LIMIT_CURR        = 0x40
	ENGINE_LIMIT_RPM         = 0x80

class MicrostepMode:
	MICROSTEP_MODE_FULL        = 0x01
	MICROSTEP_MODE_FRAC_2      = 0x02
	MICROSTEP_MODE_FRAC_4      = 0x03
	MICROSTEP_MODE_FRAC_8      = 0x04
	MICROSTEP_MODE_FRAC_16     = 0x05
	MICROSTEP_MODE_FRAC_32     = 0x06
	MICROSTEP_MODE_FRAC_64     = 0x07
	MICROSTEP_MODE_FRAC_128    = 0x08
	MICROSTEP_MODE_FRAC_256    = 0x09

class EngineType:
	ENGINE_TYPE_NONE         = 0x00
	ENGINE_TYPE_DC           = 0x01
	ENGINE_TYPE_2DC          = 0x02
	ENGINE_TYPE_STEP         = 0x03
	ENGINE_TYPE_TEST         = 0x04
	ENGINE_TYPE_BRUSHLESS    = 0x05

class DriverType:
	DRIVER_TYPE_DISCRETE_FET    = 0x01
	DRIVER_TYPE_INTEGRATE       = 0x02
	DRIVER_TYPE_EXTERNAL        = 0x03

class PowerFlags:
	POWER_REDUCT_ENABLED    = 0x01
	POWER_OFF_ENABLED       = 0x02
	POWER_SMOOTH_CURRENT    = 0x04

class SecureFlags:
	ALARM_ON_DRIVER_OVERHEATING     = 0x01
	LOW_UPWR_PROTECTION             = 0x02
	H_BRIDGE_ALERT                  = 0x04
	ALARM_ON_BORDERS_SWAP_MISSET    = 0x08
	ALARM_FLAGS_STICKING            = 0x10
	USB_BREAK_RECONNECT             = 0x20
	ALARM_WINDING_MISMATCH          = 0x40
	ALARM_ENGINE_RESPONSE           = 0x80

class PositionFlags:
	SETPOS_IGNORE_POSITION    = 0x01
	SETPOS_IGNORE_ENCODER     = 0x02

class FeedbackType:
	FEEDBACK_ENCODER             = 0x01
	FEEDBACK_EMF                 = 0x04
	FEEDBACK_NONE                = 0x05
	FEEDBACK_ENCODER_MEDIATED    = 0x06

class FeedbackFlags:
	FEEDBACK_ENC_REVERSE              = 0x01
	FEEDBACK_ENC_TYPE_BITS            = 0xC0
	FEEDBACK_ENC_TYPE_AUTO            = 0x00
	FEEDBACK_ENC_TYPE_SINGLE_ENDED    = 0x40
	FEEDBACK_ENC_TYPE_DIFFERENTIAL    = 0x80

class SyncInFlags:
	SYNCIN_ENABLED         = 0x01
	SYNCIN_INVERT          = 0x02
	SYNCIN_GOTOPOSITION    = 0x04

class SyncOutFlags:
	SYNCOUT_ENABLED     = 0x01
	SYNCOUT_STATE       = 0x02
	SYNCOUT_INVERT      = 0x04
	SYNCOUT_IN_STEPS    = 0x08
	SYNCOUT_ONSTART     = 0x10
	SYNCOUT_ONSTOP      = 0x20
	SYNCOUT_ONPERIOD    = 0x40

class ExtioSetupFlags:
	EXTIO_SETUP_OUTPUT    = 0x01
	EXTIO_SETUP_INVERT    = 0x02

class ExtioModeFlags:
	EXTIO_SETUP_MODE_IN_BITS         = 0x0F
	EXTIO_SETUP_MODE_IN_NOP          = 0x00
	EXTIO_SETUP_MODE_IN_STOP         = 0x01
	EXTIO_SETUP_MODE_IN_PWOF         = 0x02
	EXTIO_SETUP_MODE_IN_MOVR         = 0x03
	EXTIO_SETUP_MODE_IN_HOME         = 0x04
	EXTIO_SETUP_MODE_IN_ALARM        = 0x05
	EXTIO_SETUP_MODE_OUT_BITS        = 0xF0
	EXTIO_SETUP_MODE_OUT_OFF         = 0x00
	EXTIO_SETUP_MODE_OUT_ON          = 0x10
	EXTIO_SETUP_MODE_OUT_MOVING      = 0x20
	EXTIO_SETUP_MODE_OUT_ALARM       = 0x30
	EXTIO_SETUP_MODE_OUT_MOTOR_ON    = 0x40

class BorderFlags:
	BORDER_IS_ENCODER                = 0x01
	BORDER_STOP_LEFT                 = 0x02
	BORDER_STOP_RIGHT                = 0x04
	BORDERS_SWAP_MISSET_DETECTION    = 0x08

class EnderFlags:
	ENDER_SWAP              = 0x01
	ENDER_SW1_ACTIVE_LOW    = 0x02
	ENDER_SW2_ACTIVE_LOW    = 0x04

class BrakeFlags:
	BRAKE_ENABLED       = 0x01
	BRAKE_ENG_PWROFF    = 0x02

class ControlFlags:
	CONTROL_MODE_BITS                = 0x03
	CONTROL_MODE_OFF                 = 0x00
	CONTROL_MODE_JOY                 = 0x01
	CONTROL_MODE_LR                  = 0x02
	CONTROL_BTN_LEFT_PUSHED_OPEN     = 0x04
	CONTROL_BTN_RIGHT_PUSHED_OPEN    = 0x08

class JoyFlags:
	JOY_REVERSE    = 0x01

class CtpFlags:
	CTP_ENABLED             = 0x01
	CTP_BASE                = 0x02
	CTP_ALARM_ON_ERROR      = 0x04
	REV_SENS_INV            = 0x08
	CTP_ERROR_CORRECTION    = 0x10

class HomeFlags:
	HOME_DIR_FIRST           = 0x001
	HOME_DIR_SECOND          = 0x002
	HOME_MV_SEC_EN           = 0x004
	HOME_HALF_MV             = 0x008
	HOME_STOP_FIRST_BITS     = 0x030
	HOME_STOP_FIRST_REV      = 0x010
	HOME_STOP_FIRST_SYN      = 0x020
	HOME_STOP_FIRST_LIM      = 0x030
	HOME_STOP_SECOND_BITS    = 0x0C0
	HOME_STOP_SECOND_REV     = 0x040
	HOME_STOP_SECOND_SYN     = 0x080
	HOME_STOP_SECOND_LIM     = 0x0C0
	HOME_USE_FAST            = 0x100

class UARTSetupFlags:
	UART_PARITY_BITS         = 0x03
	UART_PARITY_BIT_EVEN     = 0x00
	UART_PARITY_BIT_ODD      = 0x01
	UART_PARITY_BIT_SPACE    = 0x02
	UART_PARITY_BIT_MARK     = 0x03
	UART_PARITY_BIT_USE      = 0x04
	UART_STOP_BIT            = 0x08

class MotorTypeFlags:
	MOTOR_TYPE_UNKNOWN    = 0x00
	MOTOR_TYPE_STEP       = 0x01
	MOTOR_TYPE_DC         = 0x02
	MOTOR_TYPE_BLDC       = 0x03

class EncoderSettingsFlags:
	ENCSET_DIFFERENTIAL_OUTPUT             = 0x001
	ENCSET_PUSHPULL_OUTPUT                 = 0x004
	ENCSET_INDEXCHANNEL_PRESENT            = 0x010
	ENCSET_REVOLUTIONSENSOR_PRESENT        = 0x040
	ENCSET_REVOLUTIONSENSOR_ACTIVE_HIGH    = 0x100

class MBSettingsFlags:
	MB_AVAILABLE       = 0x01
	MB_POWERED_HOLD    = 0x02

class TSSettingsFlags:
	TS_TYPE_BITS             = 0x07
	TS_TYPE_UNKNOWN          = 0x00
	TS_TYPE_THERMOCOUPLE     = 0x01
	TS_TYPE_SEMICONDUCTOR    = 0x02
	TS_AVAILABLE             = 0x08

class LSFlags:
	LS_ON_SW1_AVAILABLE    = 0x01
	LS_ON_SW2_AVAILABLE    = 0x02
	LS_SW1_ACTIVE_LOW      = 0x04
	LS_SW2_ACTIVE_LOW      = 0x08
	LS_SHORTED             = 0x10

class BackEMFFlags:
	BACK_EMF_INDUCTANCE_AUTO    = 0x01
	BACK_EMF_RESISTANCE_AUTO    = 0x02
	BACK_EMF_KM_AUTO            = 0x04


class feedback_settings_t(ctypes.Structure):
	_fields_ = [
		("IPS", ctypes.c_uint),
		("FeedbackType", ctypes.c_uint),
		("FeedbackFlags", ctypes.c_uint),
		("CountsPerTurn", ctypes.c_uint),
	]

class home_settings_t(ctypes.Structure):
	_fields_ = [
		("FastHome", ctypes.c_uint),
		("uFastHome", ctypes.c_uint),
		("SlowHome", ctypes.c_uint),
		("uSlowHome", ctypes.c_uint),
		("HomeDelta", ctypes.c_int),
		("uHomeDelta", ctypes.c_int),
		("HomeFlags", ctypes.c_uint),
	]

class home_settings_calb_t(ctypes.Structure):
	_fields_ = [
		("FastHome", ctypes.c_float),
		("SlowHome", ctypes.c_float),
		("HomeDelta", ctypes.c_float),
		("HomeFlags", ctypes.c_uint),
	]

class move_settings_t(ctypes.Structure):
	_fields_ = [
		("Speed", ctypes.c_uint),
		("uSpeed", ctypes.c_uint),
		("Accel", ctypes.c_uint),
		("Decel", ctypes.c_uint),
		("AntiplaySpeed", ctypes.c_uint),
		("uAntiplaySpeed", ctypes.c_uint),
		("MoveFlags", ctypes.c_uint),
	]

class move_settings_calb_t(ctypes.Structure):
	_fields_ = [
		("Speed", ctypes.c_float),
		("Accel", ctypes.c_float),
		("Decel", ctypes.c_float),
		("AntiplaySpeed", ctypes.c_float),
		("MoveFlags", ctypes.c_uint),
	]

class engine_settings_t(ctypes.Structure):
	_fields_ = [
		("NomVoltage", ctypes.c_uint),
		("NomCurrent", ctypes.c_uint),
		("NomSpeed", ctypes.c_uint),
		("uNomSpeed", ctypes.c_uint),
		("EngineFlags", ctypes.c_uint),
		("Antiplay", ctypes.c_int),
		("MicrostepMode", ctypes.c_uint),
		("StepsPerRev", ctypes.c_uint),
	]

class engine_settings_calb_t(ctypes.Structure):
	_fields_ = [
		("NomVoltage", ctypes.c_uint),
		("NomCurrent", ctypes.c_uint),
		("NomSpeed", ctypes.c_float),
		("EngineFlags", ctypes.c_uint),
		("Antiplay", ctypes.c_float),
		("MicrostepMode", ctypes.c_uint),
		("StepsPerRev", ctypes.c_uint),
	]

class entype_settings_t(ctypes.Structure):
	_fields_ = [
		("EngineType", ctypes.c_uint),
		("DriverType", ctypes.c_uint),
	]

class power_settings_t(ctypes.Structure):
	_fields_ = [
		("HoldCurrent", ctypes.c_uint),
		("CurrReductDelay", ctypes.c_uint),
		("PowerOffDelay", ctypes.c_uint),
		("CurrentSetTime", ctypes.c_uint),
		("PowerFlags", ctypes.c_uint),
	]

class secure_settings_t(ctypes.Structure):
	_fields_ = [
		("LowUpwrOff", ctypes.c_uint),
		("CriticalIpwr", ctypes.c_uint),
		("CriticalUpwr", ctypes.c_uint),
		("CriticalT", ctypes.c_uint),
		("CriticalIusb", ctypes.c_uint),
		("CriticalUusb", ctypes.c_uint),
		("MinimumUusb", ctypes.c_uint),
		("Flags", ctypes.c_uint),
	]

class edges_settings_t(ctypes.Structure):
	_fields_ = [
		("BorderFlags", ctypes.c_uint),
		("EnderFlags", ctypes.c_uint),
		("LeftBorder", ctypes.c_int),
		("uLeftBorder", ctypes.c_int),
		("RightBorder", ctypes.c_int),
		("uRightBorder", ctypes.c_int),
	]

class edges_settings_calb_t(ctypes.Structure):
	_fields_ = [
		("BorderFlags", ctypes.c_uint),
		("EnderFlags", ctypes.c_uint),
		("LeftBorder", ctypes.c_float),
		("RightBorder", ctypes.c_float),
	]

class pid_settings_t(ctypes.Structure):
	_fields_ = [
		("KpU", ctypes.c_uint),
		("KiU", ctypes.c_uint),
		("KdU", ctypes.c_uint),
		("Kpf", ctypes.c_float),
		("Kif", ctypes.c_float),
		("Kdf", ctypes.c_float),
	]

class sync_in_settings_t(ctypes.Structure):
	_fields_ = [
		("SyncInFlags", ctypes.c_uint),
		("ClutterTime", ctypes.c_uint),
		("Position", ctypes.c_int),
		("uPosition", ctypes.c_int),
		("Speed", ctypes.c_uint),
		("uSpeed", ctypes.c_uint),
	]

class sync_in_settings_calb_t(ctypes.Structure):
	_fields_ = [
		("SyncInFlags", ctypes.c_uint),
		("ClutterTime", ctypes.c_uint),
		("Position", ctypes.c_float),
		("Speed", ctypes.c_float),
	]

class sync_out_settings_t(ctypes.Structure):
	_fields_ = [
		("SyncOutFlags", ctypes.c_uint),
		("SyncOutPulseSteps", ctypes.c_uint),
		("SyncOutPeriod", ctypes.c_uint),
		("Accuracy", ctypes.c_uint),
		("uAccuracy", ctypes.c_uint),
	]

class sync_out_settings_calb_t(ctypes.Structure):
	_fields_ = [
		("SyncOutFlags", ctypes.c_uint),
		("SyncOutPulseSteps", ctypes.c_uint),
		("SyncOutPeriod", ctypes.c_uint),
		("Accuracy", ctypes.c_float),
	]

class extio_settings_t(ctypes.Structure):
	_fields_ = [
		("EXTIOSetupFlags", ctypes.c_uint),
		("EXTIOModeFlags", ctypes.c_uint),
	]

class brake_settings_t(ctypes.Structure):
	_fields_ = [
		("t1", ctypes.c_uint),
		("t2", ctypes.c_uint),
		("t3", ctypes.c_uint),
		("t4", ctypes.c_uint),
		("BrakeFlags", ctypes.c_uint),
	]

class control_settings_t(ctypes.Structure):
	_fields_ = [
		("MaxSpeed", ctypes.c_uint * 10),
		("uMaxSpeed", ctypes.c_uint * 10),
		("Timeout", ctypes.c_uint * 9),
		("MaxClickTime", ctypes.c_uint),
		("Flags", ctypes.c_uint),
		("DeltaPosition", ctypes.c_int),
		("uDeltaPosition", ctypes.c_int),
	]

class control_settings_calb_t(ctypes.Structure):
	_fields_ = [
		("MaxSpeed", ctypes.c_float * 10),
		("Timeout", ctypes.c_uint * 9),
		("MaxClickTime", ctypes.c_uint),
		("Flags", ctypes.c_uint),
		("DeltaPosition", ctypes.c_float),
	]

class joystick_settings_t(ctypes.Structure):
	_fields_ = [
		("JoyLowEnd", ctypes.c_uint),
		("JoyCenter", ctypes.c_uint),
		("JoyHighEnd", ctypes.c_uint),
		("ExpFactor", ctypes.c_uint),
		("DeadZone", ctypes.c_uint),
		("JoyFlags", ctypes.c_uint),
	]

class ctp_settings_t(ctypes.Structure):
	_fields_ = [
		("CTPMinError", ctypes.c_uint),
		("CTPFlags", ctypes.c_uint),
	]

class uart_settings_t(ctypes.Structure):
	_fields_ = [
		("Speed", ctypes.c_uint),
		("UARTSetupFlags", ctypes.c_uint),
	]

class network_settings_t(ctypes.Structure):
	_fields_ = [
		("DHCPEnabled", ctypes.c_uint),
		("IPv4Address", ctypes.c_uint * 4),
		("SubnetMask", ctypes.c_uint * 4),
		("DefaultGateway", ctypes.c_uint * 4),
	]

class password_settings_t(ctypes.Structure):
	_fields_ = [
		("UserPassword", ctypes.c_uint * 20),
	]

class calibration_settings_t(ctypes.Structure):
	_fields_ = [
		("CSS1_A", ctypes.c_float),
		("CSS1_B", ctypes.c_float),
		("CSS2_A", ctypes.c_float),
		("CSS2_B", ctypes.c_float),
		("FullCurrent_A", ctypes.c_float),
		("FullCurrent_B", ctypes.c_float),
	]

class controller_name_t(ctypes.Structure):
	_fields_ = [
		("ControllerName", ctypes.c_char * 17),
		("CtrlFlags", ctypes.c_uint),
	]

class nonvolatile_memory_t(ctypes.Structure):
	_fields_ = [
		("UserData", ctypes.c_uint * 7),
	]

class emf_settings_t(ctypes.Structure):
	_fields_ = [
		("L", ctypes.c_float),
		("R", ctypes.c_float),
		("Km", ctypes.c_float),
		("BackEMFFlags", ctypes.c_uint),
	]

class engine_advansed_setup_t(ctypes.Structure):
	_fields_ = [
		("stepcloseloop_Kw", ctypes.c_uint),
		("stepcloseloop_Kp_low", ctypes.c_uint),
		("stepcloseloop_Kp_high", ctypes.c_uint),
	]

class extended_settings_t(ctypes.Structure):
	_fields_ = [
		("Param1", ctypes.c_uint),
	]

class get_position_t(ctypes.Structure):
	_fields_ = [
		("Position", ctypes.c_int),
		("uPosition", ctypes.c_int),
		("EncPosition", ctypes.c_longlong),
	]

class get_position_calb_t(ctypes.Structure):
	_fields_ = [
		("Position", ctypes.c_float),
		("EncPosition", ctypes.c_longlong),
	]

class set_position_t(ctypes.Structure):
	_fields_ = [
		("Position", ctypes.c_int),
		("uPosition", ctypes.c_int),
		("EncPosition", ctypes.c_longlong),
		("PosFlags", ctypes.c_uint),
	]

class set_position_calb_t(ctypes.Structure):
	_fields_ = [
		("Position", ctypes.c_float),
		("EncPosition", ctypes.c_longlong),
		("PosFlags", ctypes.c_uint),
	]

class status_t(ctypes.Structure):
	_fields_ = [
		("MoveSts", ctypes.c_uint),
		("MvCmdSts", ctypes.c_uint),
		("PWRSts", ctypes.c_uint),
		("EncSts", ctypes.c_uint),
		("WindSts", ctypes.c_uint),
		("CurPosition", ctypes.c_int),
		("uCurPosition", ctypes.c_int),
		("EncPosition", ctypes.c_longlong),
		("CurSpeed", ctypes.c_int),
		("uCurSpeed", ctypes.c_int),
		("Ipwr", ctypes.c_int),
		("Upwr", ctypes.c_int),
		("Iusb", ctypes.c_int),
		("Uusb", ctypes.c_int),
		("CurT", ctypes.c_int),
		("Flags", ctypes.c_uint),
		("GPIOFlags", ctypes.c_uint),
		("CmdBufFreeSpace", ctypes.c_uint),
	]

class status_calb_t(ctypes.Structure):
	_fields_ = [
		("MoveSts", ctypes.c_uint),
		("MvCmdSts", ctypes.c_uint),
		("PWRSts", ctypes.c_uint),
		("EncSts", ctypes.c_uint),
		("WindSts", ctypes.c_uint),
		("CurPosition", ctypes.c_float),
		("EncPosition", ctypes.c_longlong),
		("CurSpeed", ctypes.c_float),
		("Ipwr", ctypes.c_int),
		("Upwr", ctypes.c_int),
		("Iusb", ctypes.c_int),
		("Uusb", ctypes.c_int),
		("CurT", ctypes.c_int),
		("Flags", ctypes.c_uint),
		("GPIOFlags", ctypes.c_uint),
		("CmdBufFreeSpace", ctypes.c_uint),
	]

class measurements_t(ctypes.Structure):
	_fields_ = [
		("Speed", ctypes.c_int * 25),
		("Error", ctypes.c_int * 25),
		("Length", ctypes.c_uint),
	]

class chart_data_t(ctypes.Structure):
	_fields_ = [
		("WindingVoltageA", ctypes.c_int),
		("WindingVoltageB", ctypes.c_int),
		("WindingVoltageC", ctypes.c_int),
		("WindingCurrentA", ctypes.c_int),
		("WindingCurrentB", ctypes.c_int),
		("WindingCurrentC", ctypes.c_int),
		("Pot", ctypes.c_uint),
		("Joy", ctypes.c_uint),
		("DutyCycle", ctypes.c_int),
	]

class device_information_t(ctypes.Structure):
	_fields_ = [
		("Manufacturer", ctypes.c_char * 5),
		("ManufacturerId", ctypes.c_char * 3),
		("ProductDescription", ctypes.c_char * 9),
		("Major", ctypes.c_uint),
		("Minor", ctypes.c_uint),
		("Release", ctypes.c_uint),
	]

class serial_number_t(ctypes.Structure):
	_fields_ = [
		("SN", ctypes.c_uint),
		("Key", ctypes.c_ubyte * 32),
		("Major", ctypes.c_uint),
		("Minor", ctypes.c_uint),
		("Release", ctypes.c_uint),
	]

class analog_data_t(ctypes.Structure):
	_fields_ = [
		("A1Voltage_ADC", ctypes.c_uint),
		("A2Voltage_ADC", ctypes.c_uint),
		("B1Voltage_ADC", ctypes.c_uint),
		("B2Voltage_ADC", ctypes.c_uint),
		("SupVoltage_ADC", ctypes.c_uint),
		("ACurrent_ADC", ctypes.c_uint),
		("BCurrent_ADC", ctypes.c_uint),
		("FullCurrent_ADC", ctypes.c_uint),
		("Temp_ADC", ctypes.c_uint),
		("Joy_ADC", ctypes.c_uint),
		("Pot_ADC", ctypes.c_uint),
		("L5_ADC", ctypes.c_uint),
		("H5_ADC", ctypes.c_uint),
		("A1Voltage", ctypes.c_int),
		("A2Voltage", ctypes.c_int),
		("B1Voltage", ctypes.c_int),
		("B2Voltage", ctypes.c_int),
		("SupVoltage", ctypes.c_int),
		("ACurrent", ctypes.c_int),
		("BCurrent", ctypes.c_int),
		("FullCurrent", ctypes.c_int),
		("Temp", ctypes.c_int),
		("Joy", ctypes.c_int),
		("Pot", ctypes.c_int),
		("L5", ctypes.c_int),
		("H5", ctypes.c_int),
		("deprecated", ctypes.c_uint),
		("R", ctypes.c_int),
		("L", ctypes.c_int),
	]

class debug_read_t(ctypes.Structure):
	_fields_ = [
		("DebugData", ctypes.c_ubyte * 128),
	]

class debug_write_t(ctypes.Structure):
	_fields_ = [
		("DebugData", ctypes.c_ubyte * 128),
	]

class stage_name_t(ctypes.Structure):
	_fields_ = [
		("PositionerName", ctypes.c_char * 17),
	]

class stage_information_t(ctypes.Structure):
	_fields_ = [
		("Manufacturer", ctypes.c_char * 17),
		("PartNumber", ctypes.c_char * 25),
	]

class stage_settings_t(ctypes.Structure):
	_fields_ = [
		("LeadScrewPitch", ctypes.c_float),
		("Units", ctypes.c_char * 9),
		("MaxSpeed", ctypes.c_float),
		("TravelRange", ctypes.c_float),
		("SupplyVoltageMin", ctypes.c_float),
		("SupplyVoltageMax", ctypes.c_float),
		("MaxCurrentConsumption", ctypes.c_float),
		("HorizontalLoadCapacity", ctypes.c_float),
		("VerticalLoadCapacity", ctypes.c_float),
	]

class motor_information_t(ctypes.Structure):
	_fields_ = [
		("Manufacturer", ctypes.c_char * 17),
		("PartNumber", ctypes.c_char * 25),
	]

class motor_settings_t(ctypes.Structure):
	_fields_ = [
		("MotorType", ctypes.c_uint),
		("ReservedField", ctypes.c_uint),
		("Poles", ctypes.c_uint),
		("Phases", ctypes.c_uint),
		("NominalVoltage", ctypes.c_float),
		("NominalCurrent", ctypes.c_float),
		("NominalSpeed", ctypes.c_float),
		("NominalTorque", ctypes.c_float),
		("NominalPower", ctypes.c_float),
		("WindingResistance", ctypes.c_float),
		("WindingInductance", ctypes.c_float),
		("RotorInertia", ctypes.c_float),
		("StallTorque", ctypes.c_float),
		("DetentTorque", ctypes.c_float),
		("TorqueConstant", ctypes.c_float),
		("SpeedConstant", ctypes.c_float),
		("SpeedTorqueGradient", ctypes.c_float),
		("MechanicalTimeConstant", ctypes.c_float),
		("MaxSpeed", ctypes.c_float),
		("MaxCurrent", ctypes.c_float),
		("MaxCurrentTime", ctypes.c_float),
		("NoLoadCurrent", ctypes.c_float),
		("NoLoadSpeed", ctypes.c_float),
	]

class encoder_information_t(ctypes.Structure):
	_fields_ = [
		("Manufacturer", ctypes.c_char * 17),
		("PartNumber", ctypes.c_char * 25),
	]

class encoder_settings_t(ctypes.Structure):
	_fields_ = [
		("MaxOperatingFrequency", ctypes.c_float),
		("SupplyVoltageMin", ctypes.c_float),
		("SupplyVoltageMax", ctypes.c_float),
		("MaxCurrentConsumption", ctypes.c_float),
		("PPR", ctypes.c_uint),
		("EncoderSettings", ctypes.c_uint),
	]

class hallsensor_information_t(ctypes.Structure):
	_fields_ = [
		("Manufacturer", ctypes.c_char * 17),
		("PartNumber", ctypes.c_char * 25),
	]

class hallsensor_settings_t(ctypes.Structure):
	_fields_ = [
		("MaxOperatingFrequency", ctypes.c_float),
		("SupplyVoltageMin", ctypes.c_float),
		("SupplyVoltageMax", ctypes.c_float),
		("MaxCurrentConsumption", ctypes.c_float),
		("PPR", ctypes.c_uint),
	]

class gear_information_t(ctypes.Structure):
	_fields_ = [
		("Manufacturer", ctypes.c_char * 17),
		("PartNumber", ctypes.c_char * 25),
	]

class gear_settings_t(ctypes.Structure):
	_fields_ = [
		("ReductionIn", ctypes.c_float),
		("ReductionOut", ctypes.c_float),
		("RatedInputTorque", ctypes.c_float),
		("RatedInputSpeed", ctypes.c_float),
		("MaxOutputBacklash", ctypes.c_float),
		("InputInertia", ctypes.c_float),
		("Efficiency", ctypes.c_float),
	]

class accessories_settings_t(ctypes.Structure):
	_fields_ = [
		("MagneticBrakeInfo", ctypes.c_char * 25),
		("MBRatedVoltage", ctypes.c_float),
		("MBRatedCurrent", ctypes.c_float),
		("MBTorque", ctypes.c_float),
		("MBSettings", ctypes.c_uint),
		("TemperatureSensorInfo", ctypes.c_char * 25),
		("TSMin", ctypes.c_float),
		("TSMax", ctypes.c_float),
		("TSGrad", ctypes.c_float),
		("TSSettings", ctypes.c_uint),
		("LimitSwitchesSettings", ctypes.c_uint),
	]

class init_random_t(ctypes.Structure):
	_fields_ = [
		("key", ctypes.c_ubyte * 16),
	]

class globally_unique_identifier_t(ctypes.Structure):
	_fields_ = [
		("UniqueID0", ctypes.c_uint),
		("UniqueID1", ctypes.c_uint),
		("UniqueID2", ctypes.c_uint),
		("UniqueID3", ctypes.c_uint),
	]

# Equivalent of ximc-2.14.14\ximc\python-profiles\STANDA\8MRU_1TP.py
# This code is derived from the fonction defined provided in python-profiles.
# If updated, remember to update version number above.

def set_profile_8MRU_1TP(lib, id):
    worst_result = Result.Ok
    result = Result.Ok

    feedback_settings = feedback_settings_t()

    feedback_settings.IPS = 4000
    class FeedbackType_:
        FEEDBACK_ENCODER_MEDIATED = 6
        FEEDBACK_NONE = 5
        FEEDBACK_EMF = 4
        FEEDBACK_ENCODER = 1
    feedback_settings.FeedbackType = FeedbackType_.FEEDBACK_NONE
    class FeedbackFlags_:
        FEEDBACK_ENC_TYPE_BITS = 192
        FEEDBACK_ENC_TYPE_DIFFERENTIAL = 128
        FEEDBACK_ENC_TYPE_SINGLE_ENDED = 64
        FEEDBACK_ENC_REVERSE = 1
        FEEDBACK_ENC_TYPE_AUTO = 0
    feedback_settings.FeedbackFlags = FeedbackFlags_.FEEDBACK_ENC_TYPE_SINGLE_ENDED | FeedbackFlags_.FEEDBACK_ENC_TYPE_AUTO
    feedback_settings.CountsPerTurn = 4000
    result = lib.set_feedback_settings(id, ctypes.byref(feedback_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    home_settings = home_settings_t()

    home_settings.FastHome = 100
    home_settings.uFastHome = 0
    home_settings.SlowHome = 50
    home_settings.uSlowHome = 0
    home_settings.HomeDelta = 0
    home_settings.uHomeDelta = 0
    class HomeFlags_:
        HOME_USE_FAST = 256
        HOME_STOP_SECOND_BITS = 192
        HOME_STOP_SECOND_LIM = 192
        HOME_STOP_SECOND_SYN = 128
        HOME_STOP_SECOND_REV = 64
        HOME_STOP_FIRST_BITS = 48
        HOME_STOP_FIRST_LIM = 48
        HOME_STOP_FIRST_SYN = 32
        HOME_STOP_FIRST_REV = 16
        HOME_HALF_MV = 8
        HOME_MV_SEC_EN = 4
        HOME_DIR_SECOND = 2
        HOME_DIR_FIRST = 1
    home_settings.HomeFlags = HomeFlags_.HOME_USE_FAST | HomeFlags_.HOME_STOP_SECOND_REV | HomeFlags_.HOME_STOP_FIRST_BITS | HomeFlags_.HOME_DIR_SECOND
    result = lib.set_home_settings(id, ctypes.byref(home_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    move_settings = move_settings_t()

    move_settings.Speed = 2000
    move_settings.uSpeed = 0
    move_settings.Accel = 2000
    move_settings.Decel = 5000
    move_settings.AntiplaySpeed = 2000
    move_settings.uAntiplaySpeed = 0
    class MoveFlags_:
        RPM_DIV_1000 = 1

    result = lib.set_move_settings(id, ctypes.byref(move_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    engine_settings = engine_settings_t()

    engine_settings.NomVoltage = 1
    engine_settings.NomCurrent = 670
    engine_settings.NomSpeed = 5000
    engine_settings.uNomSpeed = 0
    class EngineFlags_:
        ENGINE_LIMIT_RPM = 128
        ENGINE_LIMIT_CURR = 64
        ENGINE_LIMIT_VOLT = 32
        ENGINE_ACCEL_ON = 16
        ENGINE_ANTIPLAY = 8
        ENGINE_MAX_SPEED = 4
        ENGINE_CURRENT_AS_RMS = 2
        ENGINE_REVERSE = 1
    engine_settings.EngineFlags = EngineFlags_.ENGINE_LIMIT_RPM | EngineFlags_.ENGINE_ACCEL_ON
    engine_settings.Antiplay = 1800
    class MicrostepMode_:
        MICROSTEP_MODE_FRAC_256 = 9
        MICROSTEP_MODE_FRAC_128 = 8
        MICROSTEP_MODE_FRAC_64 = 7
        MICROSTEP_MODE_FRAC_32 = 6
        MICROSTEP_MODE_FRAC_16 = 5
        MICROSTEP_MODE_FRAC_8 = 4
        MICROSTEP_MODE_FRAC_4 = 3
        MICROSTEP_MODE_FRAC_2 = 2
        MICROSTEP_MODE_FULL = 1
    engine_settings.MicrostepMode = MicrostepMode_.MICROSTEP_MODE_FRAC_256
    engine_settings.StepsPerRev = 200
    result = lib.set_engine_settings(id, ctypes.byref(engine_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    entype_settings = entype_settings_t()

    class EngineType_:
        ENGINE_TYPE_BRUSHLESS = 5
        ENGINE_TYPE_TEST = 4
        ENGINE_TYPE_STEP = 3
        ENGINE_TYPE_2DC = 2
        ENGINE_TYPE_DC = 1
        ENGINE_TYPE_NONE = 0
    entype_settings.EngineType = EngineType_.ENGINE_TYPE_STEP | EngineType_.ENGINE_TYPE_NONE
    class DriverType_:
        DRIVER_TYPE_EXTERNAL = 3
        DRIVER_TYPE_INTEGRATE = 2
        DRIVER_TYPE_DISCRETE_FET = 1
    entype_settings.DriverType = DriverType_.DRIVER_TYPE_INTEGRATE
    result = lib.set_entype_settings(id, ctypes.byref(entype_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    power_settings = power_settings_t()

    power_settings.HoldCurrent = 50
    power_settings.CurrReductDelay = 1000
    power_settings.PowerOffDelay = 60
    power_settings.CurrentSetTime = 300
    class PowerFlags_:
        POWER_SMOOTH_CURRENT = 4
        POWER_OFF_ENABLED = 2
        POWER_REDUCT_ENABLED = 1
    power_settings.PowerFlags = PowerFlags_.POWER_SMOOTH_CURRENT | PowerFlags_.POWER_OFF_ENABLED | PowerFlags_.POWER_REDUCT_ENABLED
    result = lib.set_power_settings(id, ctypes.byref(power_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    secure_settings = secure_settings_t()

    secure_settings.LowUpwrOff = 800
    secure_settings.CriticalIpwr = 4000
    secure_settings.CriticalUpwr = 5500
    secure_settings.CriticalT = 800
    secure_settings.CriticalIusb = 450
    secure_settings.CriticalUusb = 520
    secure_settings.MinimumUusb = 420
    class Flags_:
        ALARM_ENGINE_RESPONSE = 128
        ALARM_WINDING_MISMATCH = 64
        USB_BREAK_RECONNECT = 32
        ALARM_FLAGS_STICKING = 16
        ALARM_ON_BORDERS_SWAP_MISSET = 8
        H_BRIDGE_ALERT = 4
        LOW_UPWR_PROTECTION = 2
        ALARM_ON_DRIVER_OVERHEATING = 1
    secure_settings.Flags = Flags_.ALARM_ENGINE_RESPONSE | Flags_.ALARM_FLAGS_STICKING | Flags_.ALARM_ON_BORDERS_SWAP_MISSET | Flags_.H_BRIDGE_ALERT | Flags_.ALARM_ON_DRIVER_OVERHEATING
    result = lib.set_secure_settings(id, ctypes.byref(secure_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    edges_settings = edges_settings_t()

    class BorderFlags_:
        BORDERS_SWAP_MISSET_DETECTION = 8
        BORDER_STOP_RIGHT = 4
        BORDER_STOP_LEFT = 2
        BORDER_IS_ENCODER = 1

    class EnderFlags_:
        ENDER_SW2_ACTIVE_LOW = 4
        ENDER_SW1_ACTIVE_LOW = 2
        ENDER_SWAP = 1

    edges_settings.LeftBorder = 90
    edges_settings.uLeftBorder = 0
    edges_settings.RightBorder = 3510
    edges_settings.uRightBorder = 0
    result = lib.set_edges_settings(id, ctypes.byref(edges_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    pid_settings = pid_settings_t()

    pid_settings.KpU = 0
    pid_settings.KiU = 0
    pid_settings.KdU = 0
    pid_settings.Kpf = 0.003599999938160181
    pid_settings.Kif = 0.03799999877810478
    pid_settings.Kdf = 2.8000000384054147e-05
    result = lib.set_pid_settings(id, ctypes.byref(pid_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    sync_in_settings = sync_in_settings_t()

    class SyncInFlags_:
        SYNCIN_GOTOPOSITION = 4
        SYNCIN_INVERT = 2
        SYNCIN_ENABLED = 1

    sync_in_settings.ClutterTime = 4
    sync_in_settings.Position = 0
    sync_in_settings.uPosition = 0
    sync_in_settings.Speed = 0
    sync_in_settings.uSpeed = 0
    result = lib.set_sync_in_settings(id, ctypes.byref(sync_in_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    sync_out_settings = sync_out_settings_t()

    class SyncOutFlags_:
        SYNCOUT_ONPERIOD = 64
        SYNCOUT_ONSTOP = 32
        SYNCOUT_ONSTART = 16
        SYNCOUT_IN_STEPS = 8
        SYNCOUT_INVERT = 4
        SYNCOUT_STATE = 2
        SYNCOUT_ENABLED = 1
    sync_out_settings.SyncOutFlags = SyncOutFlags_.SYNCOUT_ONSTOP | SyncOutFlags_.SYNCOUT_ONSTART
    sync_out_settings.SyncOutPulseSteps = 100
    sync_out_settings.SyncOutPeriod = 2000
    sync_out_settings.Accuracy = 0
    sync_out_settings.uAccuracy = 0
    result = lib.set_sync_out_settings(id, ctypes.byref(sync_out_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    extio_settings = extio_settings_t()

    class EXTIOSetupFlags_:
        EXTIO_SETUP_INVERT = 2
        EXTIO_SETUP_OUTPUT = 1
    extio_settings.EXTIOSetupFlags = EXTIOSetupFlags_.EXTIO_SETUP_OUTPUT
    class EXTIOModeFlags_:
        EXTIO_SETUP_MODE_OUT_BITS = 240
        EXTIO_SETUP_MODE_OUT_MOTOR_ON = 64
        EXTIO_SETUP_MODE_OUT_ALARM = 48
        EXTIO_SETUP_MODE_OUT_MOVING = 32
        EXTIO_SETUP_MODE_OUT_ON = 16
        EXTIO_SETUP_MODE_IN_BITS = 15
        EXTIO_SETUP_MODE_IN_ALARM = 5
        EXTIO_SETUP_MODE_IN_HOME = 4
        EXTIO_SETUP_MODE_IN_MOVR = 3
        EXTIO_SETUP_MODE_IN_PWOF = 2
        EXTIO_SETUP_MODE_IN_STOP = 1
        EXTIO_SETUP_MODE_IN_NOP = 0
        EXTIO_SETUP_MODE_OUT_OFF = 0
    extio_settings.EXTIOModeFlags = EXTIOModeFlags_.EXTIO_SETUP_MODE_IN_STOP | EXTIOModeFlags_.EXTIO_SETUP_MODE_IN_NOP | EXTIOModeFlags_.EXTIO_SETUP_MODE_OUT_OFF
    result = lib.set_extio_settings(id, ctypes.byref(extio_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    brake_settings = brake_settings_t()

    brake_settings.t1 = 300
    brake_settings.t2 = 500
    brake_settings.t3 = 300
    brake_settings.t4 = 400
    class BrakeFlags_:
        BRAKE_ENG_PWROFF = 2
        BRAKE_ENABLED = 1
    brake_settings.BrakeFlags = BrakeFlags_.BRAKE_ENG_PWROFF
    result = lib.set_brake_settings(id, ctypes.byref(brake_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    control_settings = control_settings_t()

    control_settings.MaxSpeed[0] = 20
    control_settings.MaxSpeed[1] = 200
    control_settings.MaxSpeed[2] = 2000
    control_settings.MaxSpeed[3] = 0
    control_settings.MaxSpeed[4] = 0
    control_settings.MaxSpeed[5] = 0
    control_settings.MaxSpeed[6] = 0
    control_settings.MaxSpeed[7] = 0
    control_settings.MaxSpeed[8] = 0
    control_settings.MaxSpeed[9] = 0
    control_settings.uMaxSpeed[0] = 0
    control_settings.uMaxSpeed[1] = 0
    control_settings.uMaxSpeed[2] = 0
    control_settings.uMaxSpeed[3] = 0
    control_settings.uMaxSpeed[4] = 0
    control_settings.uMaxSpeed[5] = 0
    control_settings.uMaxSpeed[6] = 0
    control_settings.uMaxSpeed[7] = 0
    control_settings.uMaxSpeed[8] = 0
    control_settings.uMaxSpeed[9] = 0
    control_settings.Timeout[0] = 1000
    control_settings.Timeout[1] = 1000
    control_settings.Timeout[2] = 1000
    control_settings.Timeout[3] = 1000
    control_settings.Timeout[4] = 1000
    control_settings.Timeout[5] = 1000
    control_settings.Timeout[6] = 1000
    control_settings.Timeout[7] = 1000
    control_settings.Timeout[8] = 1000
    control_settings.MaxClickTime = 300
    class Flags_:
        CONTROL_BTN_RIGHT_PUSHED_OPEN = 8
        CONTROL_BTN_LEFT_PUSHED_OPEN = 4
        CONTROL_MODE_BITS = 3
        CONTROL_MODE_LR = 2
        CONTROL_MODE_JOY = 1
        CONTROL_MODE_OFF = 0
    control_settings.Flags = Flags_.CONTROL_MODE_LR | Flags_.CONTROL_MODE_OFF
    control_settings.DeltaPosition = 1
    control_settings.uDeltaPosition = 0
    result = lib.set_control_settings(id, ctypes.byref(control_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    joystick_settings = joystick_settings_t()

    joystick_settings.JoyLowEnd = 0
    joystick_settings.JoyCenter = 5000
    joystick_settings.JoyHighEnd = 10000
    joystick_settings.ExpFactor = 100
    joystick_settings.DeadZone = 50
    class JoyFlags_:
        JOY_REVERSE = 1

    result = lib.set_joystick_settings(id, ctypes.byref(joystick_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    ctp_settings = ctp_settings_t()

    ctp_settings.CTPMinError = 3
    class CTPFlags_:
        CTP_ERROR_CORRECTION = 16
        REV_SENS_INV = 8
        CTP_ALARM_ON_ERROR = 4
        CTP_BASE = 2
        CTP_ENABLED = 1
    ctp_settings.CTPFlags = CTPFlags_.CTP_ERROR_CORRECTION
    result = lib.set_ctp_settings(id, ctypes.byref(ctp_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    uart_settings = uart_settings_t()

    uart_settings.Speed = 115200
    class UARTSetupFlags_:
        UART_STOP_BIT = 8
        UART_PARITY_BIT_USE = 4
        UART_PARITY_BITS = 3
        UART_PARITY_BIT_MARK = 3
        UART_PARITY_BIT_SPACE = 2
        UART_PARITY_BIT_ODD = 1
        UART_PARITY_BIT_EVEN = 0
    uart_settings.UARTSetupFlags = UARTSetupFlags_.UART_PARITY_BIT_EVEN
    result = lib.set_uart_settings(id, ctypes.byref(uart_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    # controller_name = controller_name_t()

    # controller_name.ControllerName = bytes([0, 113, 238, 119, 36, 0, 72, 0, 3, 0, 0, 0, 144, 108, 79, 0])
    # class CtrlFlags_:
    #     EEPROM_PRECEDENCE = 1

    # result = lib.set_controller_name(id, ctypes.byref(controller_name))

    # if result != Result.Ok:
    #     if worst_result == Result.Ok or worst_result == Result.ValueError:
    #         worst_result = result

    emf_settings = emf_settings_t()

    emf_settings.L = 0
    emf_settings.R = 0
    emf_settings.Km = 0
    class BackEMFFlags_:
        BACK_EMF_KM_AUTO = 4
        BACK_EMF_RESISTANCE_AUTO = 2
        BACK_EMF_INDUCTANCE_AUTO = 1
    emf_settings.BackEMFFlags = BackEMFFlags_.BACK_EMF_KM_AUTO | BackEMFFlags_.BACK_EMF_RESISTANCE_AUTO | BackEMFFlags_.BACK_EMF_INDUCTANCE_AUTO
    result = lib.set_emf_settings(id, ctypes.byref(emf_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    engine_advansed_setup = engine_advansed_setup_t()

    engine_advansed_setup.stepcloseloop_Kw = 50
    engine_advansed_setup.stepcloseloop_Kp_low = 1000
    engine_advansed_setup.stepcloseloop_Kp_high = 33
    result = lib.set_engine_advansed_setup(id, ctypes.byref(engine_advansed_setup))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    extended_settings = extended_settings_t()

    extended_settings.Param1 = 0
    result = lib.set_extended_settings(id, ctypes.byref(extended_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    stage_name = stage_name_t()

    stage_name.PositionerName = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    result = lib.set_stage_name(id, ctypes.byref(stage_name))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    stage_information = stage_information_t()

    stage_information.Manufacturer = bytes([0, 116, 97, 110, 100, 97, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    stage_information.PartNumber = bytes([56, 77, 82, 85, 45, 49, 84, 80, 0, 76, 69, 110, 50, 45, 50, 48, 48, 0, 48, 0, 0, 69, 65, 83])
    result = lib.set_stage_information(id, ctypes.byref(stage_information))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    stage_settings = stage_settings_t()

    stage_settings.LeadScrewPitch = 60
    stage_settings.Units = bytes([0, 101, 103, 114, 101, 101, 0, 0])
    stage_settings.MaxSpeed = 1080
    stage_settings.TravelRange = 360
    stage_settings.SupplyVoltageMin = 0
    stage_settings.SupplyVoltageMax = 0
    stage_settings.MaxCurrentConsumption = 0
    stage_settings.HorizontalLoadCapacity = 0
    stage_settings.VerticalLoadCapacity = 0
    result = lib.set_stage_settings(id, ctypes.byref(stage_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    motor_information = motor_information_t()

    motor_information.Manufacturer = bytes([0, 111, 116, 105, 111, 110, 32, 67, 111, 110, 116, 114, 111, 108, 32, 80])
    motor_information.PartNumber = bytes([0, 67, 45, 105, 45, 52, 48, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    result = lib.set_motor_information(id, ctypes.byref(motor_information))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    motor_settings = motor_settings_t()

    class MotorType_:
        MOTOR_TYPE_BLDC = 3
        MOTOR_TYPE_DC = 2
        MOTOR_TYPE_STEP = 1
        MOTOR_TYPE_UNKNOWN = 0
    motor_settings.MotorType = MotorType_.MOTOR_TYPE_STEP | MotorType_.MOTOR_TYPE_UNKNOWN
    motor_settings.ReservedField = 0
    motor_settings.Poles = 0
    motor_settings.Phases = 0
    motor_settings.NominalVoltage = 0
    motor_settings.NominalCurrent = 0
    motor_settings.NominalSpeed = 0
    motor_settings.NominalTorque = 0
    motor_settings.NominalPower = 0
    motor_settings.WindingResistance = 0
    motor_settings.WindingInductance = 0
    motor_settings.RotorInertia = 0
    motor_settings.StallTorque = 0
    motor_settings.DetentTorque = 0
    motor_settings.TorqueConstant = 0
    motor_settings.SpeedConstant = 0
    motor_settings.SpeedTorqueGradient = 0
    motor_settings.MechanicalTimeConstant = 0
    motor_settings.MaxSpeed = 5000
    motor_settings.MaxCurrent = 0
    motor_settings.MaxCurrentTime = 0
    motor_settings.NoLoadCurrent = 0
    motor_settings.NoLoadSpeed = 0
    result = lib.set_motor_settings(id, ctypes.byref(motor_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    encoder_information = encoder_information_t()

    encoder_information.Manufacturer = bytes([0, 97, 120, 111, 110, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    encoder_information.PartNumber = bytes([0, 54, 45, 69, 65, 83, 89, 45, 49, 48, 50, 52, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    result = lib.set_encoder_information(id, ctypes.byref(encoder_information))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    encoder_settings = encoder_settings_t()

    encoder_settings.MaxOperatingFrequency = 0
    encoder_settings.SupplyVoltageMin = 0
    encoder_settings.SupplyVoltageMax = 0
    encoder_settings.MaxCurrentConsumption = 0
    encoder_settings.PPR = 1000
    class EncoderSettings_:
        ENCSET_REVOLUTIONSENSOR_ACTIVE_HIGH = 256
        ENCSET_REVOLUTIONSENSOR_PRESENT = 64
        ENCSET_INDEXCHANNEL_PRESENT = 16
        ENCSET_PUSHPULL_OUTPUT = 4
        ENCSET_DIFFERENTIAL_OUTPUT = 1

    result = lib.set_encoder_settings(id, ctypes.byref(encoder_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    hallsensor_information = hallsensor_information_t()

    hallsensor_information.Manufacturer = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    hallsensor_information.PartNumber = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    result = lib.set_hallsensor_information(id, ctypes.byref(hallsensor_information))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    hallsensor_settings = hallsensor_settings_t()

    hallsensor_settings.MaxOperatingFrequency = 0
    hallsensor_settings.SupplyVoltageMin = 0
    hallsensor_settings.SupplyVoltageMax = 0
    hallsensor_settings.MaxCurrentConsumption = 0
    hallsensor_settings.PPR = 0
    result = lib.set_hallsensor_settings(id, ctypes.byref(hallsensor_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    gear_information = gear_information_t()

    gear_information.Manufacturer = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    gear_information.PartNumber = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    result = lib.set_gear_information(id, ctypes.byref(gear_information))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    gear_settings = gear_settings_t()

    gear_settings.ReductionIn = 3
    gear_settings.ReductionOut = 1
    gear_settings.RatedInputTorque = 0
    gear_settings.RatedInputSpeed = 1500
    gear_settings.MaxOutputBacklash = 0
    gear_settings.InputInertia = 0
    gear_settings.Efficiency = 0
    result = lib.set_gear_settings(id, ctypes.byref(gear_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    accessories_settings = accessories_settings_t()

    accessories_settings.MagneticBrakeInfo = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    accessories_settings.MBRatedVoltage = 0
    accessories_settings.MBRatedCurrent = 0
    accessories_settings.MBTorque = 0
    class MBSettings_:
        MB_POWERED_HOLD = 2
        MB_AVAILABLE = 1

    accessories_settings.TemperatureSensorInfo = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    accessories_settings.TSMin = 0
    accessories_settings.TSMax = 0
    accessories_settings.TSGrad = 0
    class TSSettings_:
        TS_AVAILABLE = 8
        TS_TYPE_BITS = 7
        TS_TYPE_SEMICONDUCTOR = 2
        TS_TYPE_THERMOCOUPLE = 1
        TS_TYPE_UNKNOWN = 0
    accessories_settings.TSSettings = TSSettings_.TS_TYPE_THERMOCOUPLE | TSSettings_.TS_TYPE_UNKNOWN
    class LimitSwitchesSettings_:
        LS_SHORTED = 16
        LS_SW2_ACTIVE_LOW = 8
        LS_SW1_ACTIVE_LOW = 4
        LS_ON_SW2_AVAILABLE = 2
        LS_ON_SW1_AVAILABLE = 1

    result = lib.set_accessories_settings(id, ctypes.byref(accessories_settings))

    if result != Result.Ok:
        if worst_result == Result.Ok or worst_result == Result.ValueError:
            worst_result = result

    return worst_result
