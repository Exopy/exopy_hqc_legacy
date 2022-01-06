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
        self._header_osc_freq = (
        '/'+device+'/oscs/{}/freq'.format(channel_num-1))

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
            raise InstrIOError('The instrument did not '
                               'set frequency correctly')

class HF2LIDemodChannel(BaseInstrument):

    def __init__(self, LI, channel_num, caching_allowed=True,
                 caching_permissions={}, device=''):
        super(HF2LIDemodChannel, self).__init__(None, caching_allowed,
                                              caching_permissions)
        self._LI = LI
        self._channel = channel_num
        self._device_id = device
        self._header_demod_sample = (
        '/' + device + '/demods/{}/sample'.format(channel_num-1))
        self._header_demod_osc = (
        '/' + device + '/demods/{}/oscselect'.format(channel_num-1))
        self._header_demod_harm = (
        '/' + device + '/demods/{}/harmonic'.format(channel_num-1))
        self._header_demod_phase = (
        '/' + device + '/demods/{}/phaseshift'.format(channel_num-1))       
        self._header_demod_timeconstant = (
        '/' + device + '/demods/{}/timeconstant'.format(channel_num-1))
        self._header_demod_order = (
        '/' + device + '/demods/{}/order'.format(channel_num-1))
        self._header_demod_datarate = (
        '/' + device + '/demods/{}/rate'.format(channel_num-1))

    def reopen_connection(self):

        self._LI.reopen_connection()

    def set_demod_osc(self,osc):
        """
        Set the osc select for LI demodulation by the instrument

        """
        if self._channel>5:
            raise ValueError('The instrument can only set osc for chans 1-6')
        self._LI.daq_serv.setInt(self._header_demod_osc, osc-1)
        self._LI.daq_serv.echoDevice(self._device_id)
        value=self._LI.daq_serv.getInt(self._header_demod_osc)
        if int(value)!=int(osc-1):
            raise InstrIOError('The instrument did not set osc correctly')

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

    def get_nepbw(self):
        """
        Returns the nepbw specified for the channel

        """
        if self._channel>5:
            raise ValueError('The instrument can only spec BW for chans 1-6')
        tc=self._LI.daq_serv.getDouble(self._header_demod_timeconstant)
        order=self._LI.daq_serv.getInt(self._header_demod_order)
        return self._LI.get_FO_f_nepbw(order)/tc

    def set_datarate(self, rate):
        """
        Sets the datarate for the channel

        """
        if self._channel>5:
            raise ValueError('The instrument can only set rate for chans 1-6')
        self._LI.daq_serv.setDouble(self._header_demod_datarate, rate)

    def read_x(self):
        """
        Return the x quadrature measured by the instrument

        Perform a direct reading without any waiting. Can return non
        independent values if the instrument is queried too often.

        """
        return self._LI.daq_serv.getSample(self._header_demod_sample)['x'][0]

    def read_y(self):
        """
        Return the y quadrature measured by the instrument

        Perform a direct reading without any waiting. Can return non
        independent values if the instrument is queried too often.

        """
        return self._LI.daq_serv.getSample(self._header_demod_sample)['y'][0] 

    def read_xy(self):
        """
        Return the x and y quadratures measured by the instrument

        Perform a direct reading without any waiting. Can return non
        independent values if the instrument is queried too often.

        """
        return (self._LI.daq_serv.getSample(self._header_demod_sample)['x'][0],
                self._LI.daq_serv.getSample(self._header_demod_sample)['y'][0])

    def read_amplitude(self):
        """
        Return the amplitude of the signal measured by the instrument

        Perform a direct reading without any waiting. Can return non
        independent values if the instrument is queried too often.

        """
        x=self._LI.daq_serv.getSample(self._header_demod_sample)['x'][0]
        y=self._LI.daq_serv.getSample(self._header_demod_sample)['y'][0]
        return np.sqrt(x**2+y**2)

    def read_phase(self):
        """
        Return the phase of the signal measured by the instrument

        Perform a direct reading without any waiting. Can return non
        independent values if the instrument is queried too often.

        """
        x=self._LI.daq_serv.getSample(self._header_demod_sample)['x'][0]
        y=self._LI.daq_serv.getSample(self._header_demod_sample)['y'][0]
        return np.arctan2(y,x)*180/np.pi

    def read_amp_and_phase(self):
        """
        Return the amplitude and phase of the signal measured by the instrument

        Perform a direct reading without any waiting. Can return non
        independent values if the instrument is queried too often.

        """
        x=self._LI.daq_serv.getSample(self._header_demod_sample)['x'][0]
        y=self._LI.daq_serv.getSample(self._header_demod_sample)['y'][0]
        return (np.sqrt(x**2+y**2),np.arctan2(y,x)*180/np.pi)

    @secure_communication()
    def read_xstddev(self):
        """
        Not implemented

        """
        raise RuntimeError('This command is not yet implemented'
                           'for the instrument')

    @secure_communication()
    def read_ystddev(self):
        """
        Not implemented

        """
        raise RuntimeError('This command is not yet implemented'
                           'for the instrument')

class HF2LIOutChannel(BaseInstrument):

    def __init__(self, LI, channel_num, caching_allowed=True,
                 caching_permissions={}, device=''):
        super(HF2LIOutChannel, self).__init__(None, caching_allowed,
                                              caching_permissions)
        self._LI = LI
        self._channel = channel_num
        self._device_id = device
        self._header_outampl = (
                '/'+device+'/sigouts/{}/amplitudes/'.format(channel_num-1))
        self._header_range = (
                '/'+device+'/sigouts/{}/range'.format(channel_num-1))

    def reopen_connection(self):

        self._LI.reopen_connection()

    def set_out_amplitude(self, amplmV, fromdemod=None):
        """
        Set the output amplitude from demod # for the channel 

        """
        Vrange=self._LI.daq_serv.getDouble(self._header_range)
        ampl=1e-3*amplmV/Vrange
        self._LI.daq_serv.setDouble(
                self._header_outampl+'{}'.format(fromdemod-1), ampl)
        self._LI.daq_serv.echoDevice(self._device_id)
        value=self._LI.daq_serv.getDouble(
                self._header_outampl+'{}'.format(fromdemod-1))
        if abs(value-ampl)*Vrange>1e-7:
            raise InstrIOError('The instrument did not '
                               'set amplitude correctly')

    def get_out_range(self):
        """
        Get the output range for the output channel

        """
        return self._LI.daq_serv.getDouble(self._header_range)      

class HF2LISweeper(BaseInstrument):

    log_prefix= 'ZI Sweeper: '

    def __init__(self, LI, caching_allowed=True,
                 caching_permissions={}, device=''):
        super(HF2LISweeper, self).__init__(None, caching_allowed,
                                              caching_permissions)
        self._LI = LI
        self._device_id = device
        self.suscribed = []
        self.sweeper = self._LI.daq_serv.sweep()
        self.sweeper.set('device', device)
        self.sweeper.set('historylength', 1)

    def reopen_connection(self):

        self._LI.reopen_connection()

    def set_sweep_param(self, sweep_type, sweep_channel, measkey, start, stop,
                    points, log_sweep, sweep_channel_sec = 1, avg_time = 0):
        """
        Run a sweep of parameter

        """
        if sweep_type == 'Output':
            if int(sweep_channel)>2:
                msg = 'No channel {} for output, only channels 1--2 exist'
                raise KeyError(msg.format(num))
            if int(sweep_channel_sec)>8:
                msg = 'No channel {} for output ampl., only channels 1--8 exist'
                raise KeyError(msg.format(num))                
            self.sweeper.set('gridnode', '/{}/sigouts/{}/amplitudes/{}'.format(
                self._device_id, sweep_channel-1, sweep_channel_sec-1
            ))
        else:
            if int(sweep_channel)>6:
                msg = 'No channel {} for oscillators, only channels 1--6 exist'
                raise KeyError(msg.format(num))
            self.sweeper.set('gridnode', '/{}/oscs/{}/freq'.format(
                self._device_id, sweep_channel-1
                ))
        self.sweeper.set('xmapping', log_sweep)
        if sweep_type == 'Output':
            Vrange=self._LI.get_out_channel(sweep_channel).get_out_range()
            self.sweeper.set('start', start/Vrange)
            self.sweeper.set('stop', stop/Vrange)
        else:
            self.sweeper.set('start', start)
            self.sweeper.set('stop', stop)
        self.sweeper.set('samplecount', points)
        self.sweeper.set('bandwidthcontrol', 0)
        self.sweeper.set('settling/inaccuracy', 0.0001)
        self.sweeper.set('omegasuppression', 40)
        self.sweeper.set('order', 4)
        if avg_time != 0:
            self.sweeper.set('averaging/time', avg_time)
        for ii, (chan,code) in enumerate(measkey):
            log = logging.getLogger(__name__)
            msg = ('Suscribed meas are %s')
            log.info(self.log_prefix+msg,'; '.join(map(str, (chan,code))))
            if chan not in self.suscribed:
                self.sweeper.subscribe(
                '/{}/demods/{}/sample'.format(self._device_id,int(chan)-1))
                self.suscribed.append(chan)
        log = logging.getLogger(__name__)
        msg = ('Suscribed chans are %s')
        log.info(self.log_prefix+msg,'; '.join(map(str, self.suscribed)))
        nepbws=[]
        for ii, (chan,code) in enumerate(measkey):
            chan_driver=self._LI.get_demod_channel(int(chan))
            nepbws.append(chan_driver.get_nepbw())
        if nepbws == []:
            msg = 'No read channels are selected'
            raise KeyError(msg)
        if nepbws.count(nepbws[0]) != len(nepbws):
            msg = 'Not all channels have same bandwidth for sweep'
            raise ValueError(msg)
        for ii, (chan,code) in enumerate(measkey):
            chan_driver=self._LI.get_demod_channel(int(chan))
            chan_driver.set_datarate(10*nepbws[ii])
        self.sweeper.set('endless', 0)
        self.sweeper.set('loopcount',1)

    def sweep_exec(self):
        self.sweeper.execute()

    def sweep_finished(self):
        r_time=self.sweeper.getDouble('remainingtime')
        prog=self.sweeper.progress()
        log = logging.getLogger(__name__)
        msg = ('Achieved sweep prop: {} (remains {:.3f} s)')
        log.info(self.log_prefix+msg.format(prog,r_time))
        return self.sweeper.finished()

    def read_data(self, sweep_type, sweep_channel, measkey):
        if not self.sweep_finished():
            self.sweeper.finish()
        datastruct=self.sweeper.read()
        self.sweeper.set('clearhistory', 1)
        self.sweeper.unsubscribe('*')
        final_dict = {}
        for ii, (chan,code) in enumerate(measkey):
            sample=datastruct[
            self._device_id.lower()][
            'demods'][
            str(int(chan)-1)][
            'sample']
            sample=sample[0][0]
            if final_dict == {}:
                if sweep_type == 'Output':
                    Vrange=self._LI.get_out_channel(
                            sweep_channel).get_out_range()                
                    final_dict['sweep_param']=sample['grid']*Vrange
                else:
                    final_dict['sweep_param']=sample['grid']
            if code != '':
                final_dict[chan+code]=sample[code]
            else:
                final_dict[chan]=sample['x']+1.0j*sample['y']
        return final_dict

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
        self.sweeper = None
        self._setup_api_session_identification()

        if auto_open:
            self.open_connection()

        self.osc_channels = {}
        self.demod_channels = {}
        self.out_channels = {}

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
            raise ValueError(
            'No instrument with serial id %s' % self._infos['instr_id']
            )

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

    def get_sweeper(self):
        """Returns a sweeper interface to ZI API

        """
        if self.sweeper is None:
            self.sweeper = HF2LISweeper(self, device='{}'.format(self._id))
        return self.sweeper

    def get_osc_channel(self, num):
        """num is an int identifying the osc channel 
        """
        if num not in range(1,7):
            msg = 'No channel {}, only channels 1--6 exist'
            raise KeyError(msg.format(num))

        if num in self.osc_channels:
            return self.osc_channels[num]
        else:
            channel = HF2LIOscChannel(self, 
                                      num, 
                                      device='{}'.format(self._id))
            self.osc_channels[num] = channel
            return channel

    def get_demod_channel(self, num):
        """num is an int identifying the osc channel 
        """
        if num not in range(1,9):
            msg = 'No channel {}, only channels 1--8 exist'
            raise KeyError(msg.format(num))

        if num in self.demod_channels:
            return self.demod_channels[num]
        else:
            channel = HF2LIDemodChannel(self, 
                                        num, 
                                        device='{}'.format(self._id))
            self.demod_channels[num] = channel
            return channel

    def get_out_channel(self, num):
        """num is an int identifying the out channel 
        """
        if num not in range(1,3):
            msg = 'No channel {}, only out channels 1--2 exist'
            raise KeyError(msg.format(num))

        if num in self.out_channels:
            return self.out_channels[num]
        else:
            channel = HF2LIOutChannel(self, 
                                        num, 
                                        device='{}'.format(self._id))
            self.out_channels[num] = channel
            return channel

    def _setup_api_session_identification(self):
        """Load and initialize the API session.

        """
        self._id = self._infos.get('instr_id')

    def get_FO_f_cutoff(self, order):
        '''Returns conversion factor between TC and cutoff freq
        
        '''
        FO_list=np.array([1.0000,
                          0.6436,
                          0.5098,
                          0.4350,
                          0.3856,
                          0.3499,
                          0.3226,
                          0.3008])/(2*np.pi)
        return(FO_list[order-1])

    def get_FO_f_nepbw(self, order):
        '''Returns conversion factor between TC and nepbw freq
        
        '''
        FO_list=np.array([0.2500,
                          0.1250,
                          0.0937,
                          0.0781,
                          0.0684,
                          0.0615,
                          0.0564,
                          0.0524])
        return(FO_list[order-1])
