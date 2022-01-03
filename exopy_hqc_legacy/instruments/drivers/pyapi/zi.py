# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2022 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Driver for the Zurich Insturments HF2LI.

"""
import os
import time
import numpy as np
import zhinst.ziPython
import zhinst.utils
import logging

from inspect import cleandoc

from ..driver_tools import (InstrIOError, secure_communication,
                            instrument_property)

from ..pyapi_tools import (BaseInstrument,PyAPIInstrument)


class L1ControlUnit(object):
    """Control unit for the ZI devices.

    """

    _instance = None

    log_prefix= 'ZI L1 control Driver: '

    def __new__(cls, library, utils):
        if cls._instance is not None:
            return cls._instance

        self = super(L1ControlUnit, cls).__new__(cls)
        self.library = library
        self.utils = utils
        self.discovery = library.ziDiscovery()
        log = logging.getLogger(__name__)
        msg = ('Connected instruments are %s')
        log.info(self.log_prefix+msg,'; '.join(self.list_instrs()))
        self.apilevel = 1
        self.debuglevel = 0
        self._addresses = []
        self._sessions = []
        self._devices = []
        cls._instance = self
        return self

    def list_instrs(self):
        """List the detected instruments.

        """
        res = self.discovery.findAll()
        return res

    def get_props(self,instr_id):
        """Return connection properties for one specific instrument.

        """
        return self.discovery.get(instr_id)

    def setup_instr(self, props):
        """Prepare an API session for communication with instrument instr_id 
        and return its index.

        """
        if props['serveraddress'] not in self._addresses:
            api_session = self.library.ziDAQServer(
                props['serveraddress'], props['serverport'], props['apilevel']
            )
            assert self.utils.utils.api_server_version_check(api_session)
            self._addresses.append(props['serveraddress'])
            self._sessions.append(api_session)
            self._devices.append([])
            ad_ind=self._addresses.index(props['serveraddress'])
        else:
            ad_ind=self._addresses.index(props['serveraddress'])
            api_session=self._sessions[ad_ind]
        api_session.connectDevice(props['deviceid'], props['interfaces'][0])
        self._devices[ad_ind].append(props['deviceid'])    
        
        return ad_ind

    def unsetup_instr(self, daq, instr_id):
        """close the API session for communication with instrument instr_id 
        and return its index.

        """
        if daq in self._sessions:
            sess_ind = self._sessions.index(daq)
        self._sessions[sess_ind].disconnectDevice(instr_id)
        self._devices[sess_ind].remove(instr_id)
        
        return sess_ind

    def is_connected(self, daq, instr_id):
        if daq in self._sessions:
            ad_ind = self._sessions.index(daq)
            if instr_id in self._devices[ad_ind]:
                return True
        return False

    def enable_logging(self, daq):
        """
        """
        daq.setDebugLevel(self.debuglevel)

class HF2LIOscChannel(BaseInstrument):

    def __init__(self, LI, channel_num, caching_allowed=True,
                 caching_permissions={}, device=''):
        super(HF2LIOscChannel, self).__init__(None, caching_allowed,
                                              caching_permissions)
        self._LI = LI
        self._channel = channel_num
        self._device_id = device
        self._header_osc_freq = '/'+device+'/oscs/{}/freq'.format(channel_num-1)

    def reopen_connection(self):

        self._LI.reopen_connection()

    def set_osc_frequency(self, frequency):
        """
        Set the frequency (in Hz) outputted by the instrument

        """
        self._LI.daq_serv.setDouble(self._header_osc_freq, frequency)
        self._LI.daq_serv.echoDevice(self._device_id)
        value=self._LI.daq_serv.getDouble(self._header_osc_freq)
        if abs(value-frequency)>1e-6:
            raise InstrIOError('The instrument did not set frequency correctly')

class HF2LIDemodChannel(BaseInstrument):

    def __init__(self, LI, channel_num, caching_allowed=True,
                 caching_permissions={}, device=''):
        super(HF2LIDemodChannel, self).__init__(None, caching_allowed,
                                              caching_permissions)
        self._LI = LI
        self._channel = channel_num
        self._device_id = device
        self._header_demod_harm = '/'+device+'/demods/{}/harmonic'.format(channel_num-1)
        self._header_demod_phase = '/'+device+'/demods/{}/phaseshift'.format(channel_num-1)        

    def reopen_connection(self):

        self._LI.reopen_connection()

    def set_demod_harmonic(self, harm):
        """
        Set the harmonic for LI demodulation by the instrument

        """
        if self._channel>5:
            raise ValueError('The instrument can only set harm for chans 1-6')
        self._LI.daq_serv.setDouble(self._header_demod_harm, harm)
        self._LI.daq_serv.echoDevice(self._device_id)
        value=self._LI.daq_serv.getDouble(self._header_demod_harm)
        if int(value)!=int(harm):
            raise InstrIOError('The instrument did not set harmonic correctly')

    def set_demod_phase(self, phase):
        """
        Set the phase for LI demodulation by the instrument

        """
        if self._channel>5:
            raise ValueError('The instrument can only set phase for chans 1-6')
        self._LI.daq_serv.setDouble(self._header_demod_phase, phase)
        self._LI.daq_serv.echoDevice(self._device_id)
        value=self._LI.daq_serv.getDouble(self._header_demod_phase)
        if abs(value-phase)>1e-3:
            raise InstrIOError('The instrument did not set phase correctly')

class HF2LI(PyAPIInstrument):
    """Driver for the Zurich Instrument HF2LI

    """

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(HF2LI, self).__init__(connection_info, caching_allowed,
                                      caching_permissions, auto_open)
        self._infos = connection_info
        self.cu_id = None
        self._id = None
        self.daq_serv = None
        self._setup_api_session_identification()

        if auto_open:
            self.open_connection()

        self.osc_channels = {}
        self.demod_channels = {}

    def open_connection(self):
        """Setup the right instrument based on the vendor id.

        """
        cu = L1ControlUnit(zhinst.ziPython,zhinst.utils)
        instrs = cu.list_instrs()
        serv_index = None
        for instr_id in instrs:
            if instr_id == self._id:
                props = cu.get_props(self._id)
                serv_index = cu.setup_instr(props)
                break

        if serv_index is None:
            raise ValueError('No instrument with serial id %s' % self._infos['instr_id'])

        self.daq_serv = cu._sessions[serv_index]
        cu.enable_logging(self.daq_serv)
        self.cu_id = cu

    def close_connection(self):
        """Disconnect the instrument from the acquisition server

        """
        self.cu_id.unsetup_instr(self.daq_serv,self._id)
        return True

    def reopen_connection(self):
        """Reopen the connection with the instrument, using in principle
        same DAQserver as previously.

        """
        self.close_connection()
        self.open_connection()

    def connected(self):
        """Returns whether commands can be sent to the instrument
        """
        return cu_id.is_connected(self.daq_serv,self._id)

    def basestate_instr(self):
        """Set all functions to off.

        """
        self.cu_id.utils.utils.disable_everything(self.daq_serv, self._id)

    def get_osc_channel(self, num):
        """num is an int identifying the osc channel 
        """
        if num not in range(1,7):
            msg = 'No channel {}, only channels 1--6 exist'
            raise KeyError(msg.format(num, defined))

        if num in self.osc_channels:
            return self.osc_channels[num]
        else:
            channel = HF2LIOscChannel(self, num, device='{}'.format(self._id))
            self.osc_channels[num] = channel
            return channel

    def get_demod_channel(self, num):
        """num is an int identifying the osc channel 
        """
        if num not in range(1,9):
            msg = 'No channel {}, only channels 1--8 exist'
            raise KeyError(msg.format(num, defined))

        if num in self.demod_channels:
            return self.demod_channels[num]
        else:
            channel = HF2LIDemodChannel(self, num, device='{}'.format(self._id))
            self.demod_channels[num] = channel
            return channel

    def _setup_api_session_identification(self):
        """Load and initialize the APi session.

        """
        self._id = self._infos.get('instr_id')
