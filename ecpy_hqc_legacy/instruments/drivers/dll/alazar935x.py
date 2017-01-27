# -*- coding: utf-8 -*-
# =============================================================================
# module : alazar935x.py
# author : Benjamin Huard & Nathanael Cottet & Sébastien Jezouin
# license : MIT license
# =============================================================================
"""

This module defines drivers for Alazar using DLL Library.

:Contains:
    Alazar935x

To read well the Dll of the Alazar9351, Visual C++ Studio is needed.

"""
import os
import time
import math
from subprocess import call
from inspect import cleandoc

import numpy as np
from pyclibrary import CLibrary

from ..dll_tools import DllInstrument
from ..driver_tools import InstrIOError
import atsapi as ats

# TODO : getting it ot work
# - properly get the headers directory and dll directory see sp_adq14 _setup_librar, we have three headers not just one
# -

# TODO : cleanup
# - remove DMABuffer use numpy array instead
# - clean long lines

class Alazar935x(DllInstrument):

    library = 'ATSApi.dll'

    def __init__(self, connection_infos, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(Alazar935x, self).__init__(connection_infos, caching_allowed,
                                         caching_permissions, auto_open)

        cache_path = unicode(os.path.join(os.path.dirname(__file__),
                                          'Alazar.pycctypes.libc'))
        headers = [os.path.join(connection_infos.get('header_dir', ''), h)
                   for h in ['AlazarError.h', 'AlazarCmd.h', 'AlazarApi.h']]

        self.board = ats.Board()

    def open_connection(self):
        """Do not need to open a connection

        """
        try:
            call("TASKKILL /F /IM AlazarDSO.exe", shell=True)
        except Exception:
            pass

    def close_connection(self):
        """Do not need to close a connection

        """
        pass

    def configure_board(self):

        board = self.board
        # TODO: Select clock parameters as required to generate this
        # sample rate
        self.samplesPerSec = 500000000
        board.setCaptureClock(    ats.EXTERNAL_CLOCK_10MHz_REF, # ZL: changed from EXTERNAL_CLOCK_10MHz_REF
                                  500e6, # ZL: changed from 500000000
                                  ats.CLOCK_EDGE_RISING,
                                  1)
        # TODO: Select channel A input parameters as required.
        board.inputControl(ats.CHANNEL_A,
                           ats.AC_COUPLING,
                           ats.INPUT_RANGE_PM_100_MV,
                           ats.IMPEDANCE_50_OHM)

        # TODO: Select channel A bandwidth limit as required.
        board.setBWLimit(ats.CHANNEL_A, 0)


        # TODO: Select channel B input parameters as required.
        board.inputControl(ats.CHANNEL_B,
                               ats.AC_COUPLING,
                               ats.INPUT_RANGE_PM_40_MV,
                               ats.IMPEDANCE_50_OHM)

        # TODO: Select channel B bandwidth limit as required.
        board.setBWLimit(ats.CHANNEL_B, 0)
        # TODO: Select trigger inputs and levels as required.
#        trigLevel = 0.3 # in Volts
#        trigRange = 2.5 # in Volts (Set in SetExternalTrigger() below)
#        trigCode = int(128 + 127 * trigLevel / trigRange)
        board.setTriggerOperation(ats.TRIG_ENGINE_OP_J,
                                  ats.TRIG_ENGINE_J,
                                  ats.TRIG_EXTERNAL,
                                  ats.TRIGGER_SLOPE_POSITIVE,
                                  150,
                                  ats.TRIG_ENGINE_K,
                                  ats.TRIG_DISABLE,
                                  ats.TRIGGER_SLOPE_POSITIVE,
                                  128)
        # TODO: Select external trigger parameters as required.
        board.setExternalTrigger(ats.DC_COUPLING,
                                     ats.ETR_5V)

        # TODO: Set trigger delay as required.
        triggerDelay_sec = 0.
        triggerDelay_samples = int(triggerDelay_sec * self.samplesPerSec + 0.5)
        board.setTriggerDelay(triggerDelay_samples)

        # TODO: Set trigger timeout as required.
        #
        # NOTE: The board will wait for a for this amount of time for a
        # trigger event.  If a trigger event does not arrive, then the
        # board will automatically trigger. Set the trigger timeout value
        # to 0 to force the board to wait forever for a trigger event.
        #
        # IMPORTANT: The trigger timeout value should be set to zero after
        # appropriate trigger parameters have been determined, otherwise
        # the board may trigger if the timeout interval expires before a
        # hardware trigger event arrives.
        triggerTimeout_sec = 0.
        triggerTimeout_clocks = int(triggerTimeout_sec / 10e-6 + 0.5)
        board.setTriggerTimeOut(0)

        # Configure AUX I/O connector as required
        board.configureAuxIO(ats.AUX_OUT_TRIGGER,
                             0)

#    def get_traces(self, timeaftertrig, recordsPerCapture,
#                   recordsPerBuffer, average, verbose=False):
    def get_traces(self, channels, duration, delay, records_per_capture,
                   retry=True, average=0):

        board = self.board
        verbose = False
        timeaftertrig = duration
        recordsPerCapture = records_per_capture
        samplesPerSec = 500e6

        # both channels are always acquired
        channels = ats.CHANNEL_A | ats.CHANNEL_B
        channelCount = 0
        for c in ats.channels:
            channelCount += (c & channels == c)

        postTriggerSamples = int(samplesPerSec*timeaftertrig)
        if postTriggerSamples % 32 == 0:
            postTriggerSamples = int(postTriggerSamples)
        else:
            postTriggerSamples = int((postTriggerSamples)/32 + 1)*32
        # determine the number of records per buffer
        memorySize_samples, bitsPerSample = board.getChannelInfo()
        memorySize_samples_per_chann = memorySize_samples.value/2
        total_number_samples = postTriggerSamples * recordsPerCapture

        # No pre-trigger samples in NPT mode
        preTriggerSamples = 0
        bytesPerSample = (bitsPerSample.value + 7) // 8
        samplesPerRecord = preTriggerSamples + postTriggerSamples
        bytesPerRecord = bytesPerSample * samplesPerRecord

        bytesPerBufferMax = 1e6 # See remark page 93 in ATS-SDK-Guide 7.1.4
                                # + following email exchange with Alazar engineer Romain Deterre
        recordsPerBuffer = np.min([int(math.floor(bytesPerBufferMax / (bytesPerRecord * channelCount))),recordsPerCapture])
        bytesPerBuffer = bytesPerRecord * recordsPerBuffer * channelCount

#        while total_number_samples/buffersPerAcquisition > memorySize_samples_per_chann and 1==0:
#            buffersPerAcquisition+=1

        delay = 0

        buffersPerAcquisition = int(math.ceil(float(recordsPerCapture) / recordsPerBuffer))
        records_to_ignore = buffersPerAcquisition*recordsPerBuffer - recordsPerCapture
#        print('recordsPerCapture = %s' %recordsPerCapture)
#        print('recordsPerBuffer = %s' %recordsPerBuffer)
#        print('buffersPerAcquisition = %s' %buffersPerAcquisition)
#        print('records_to_ignore = %s' %records_to_ignore)


        # Compute the number of bytes per record and per buffer



        # TODO: Select number of DMA buffers to allocate
        bufferCount = 4

        # Allocate DMA buffers
        buffers = []
        for i in range(bufferCount):
            buffers.append(ats.DMABuffer(bytesPerSample, bytesPerBuffer))

        # Set the record size
        board.setRecordSize(preTriggerSamples, postTriggerSamples)

        # I need to define a "new" recordsPerAcquisition which is an integer
        # number of recordsPerBuffer, otherwise Alazar throws an error
        # We will take care of this below
        recordsPerAcquisition = recordsPerBuffer * buffersPerAcquisition

        # Configure the board to make an NPT AutoDMA acquisition
        board.beforeAsyncRead(channels,
                              -preTriggerSamples,
                              samplesPerRecord,
                              recordsPerBuffer,
                              recordsPerAcquisition,
                              ats.ADMA_EXTERNAL_STARTCAPTURE | ats.ADMA_NPT)

        # Post DMA buffers to board
        for buffer in buffers:
            board.postAsyncBuffer(buffer.addr, buffer.size_bytes)

        start = time.clock() # Keep track of when acquisition started
        board.startCapture() # Start the acquisition
        buffersCompleted = 0
        bytesTransferred = 0

        dataA = np.empty((recordsPerCapture, samplesPerRecord))
        dataB = np.empty((recordsPerCapture, samplesPerRecord))

        while buffersCompleted < buffersPerAcquisition:

            # Wait for the buffer at the head of the list of available
            # buffers to be filled by the board.
            buffer = buffers[buffersCompleted % len(buffers)]
            board.waitAsyncBufferComplete(buffer.addr, timeout_ms=5000)
            data = np.reshape(buffer.buffer, (recordsPerBuffer*channelCount, -1))

            # making sure we only grab the number of records we asked for
            records_to_ignore_val = 0 if buffersCompleted < buffersPerAcquisition-1  else records_to_ignore
#            print(records_to_ignore_val)
#            print(np.shape(dataA[buffersCompleted*recordsPerBuffer:(buffersCompleted+1)*recordsPerBuffer-records_to_ignore_val]),np.shape(data[:recordsPerBuffer-records_to_ignore_val]))
            dataA[buffersCompleted*recordsPerBuffer:(buffersCompleted+1)*recordsPerBuffer-records_to_ignore_val] = data[:recordsPerBuffer-records_to_ignore_val]
            dataB[buffersCompleted*recordsPerBuffer:(buffersCompleted+1)*recordsPerBuffer-records_to_ignore_val] = data[recordsPerBuffer:2*recordsPerBuffer-records_to_ignore_val]

            buffersCompleted += 1
            bytesTransferred += buffer.size_bytes

            # Update progress bar

            # Add the buffer to the end of the list of available buffers.
            board.postAsyncBuffer(buffer.addr, buffer.size_bytes)

        transferTime_sec = time.clock() - start
        buffersPerSec = 0
        bytesPerSec = 0
        recordsPerSec = 0
        if transferTime_sec > 0:
            buffersPerSec = buffersCompleted / transferTime_sec
            bytesPerSec = bytesTransferred / transferTime_sec
            recordsPerSec = recordsPerBuffer * buffersCompleted / transferTime_sec

        # Abort transfer.
        board.abortAsyncRead()

#        # Re-shaping of the data for demodulation and demodulation
#        dataA = dataA[:,1:samplesPerRecord + 1]
#        dataB = dataB[:,1:samplesPerRecord + 1]
#
#                # Averaging if needed and converting binary numbers into Volts
#        if average:
#            dataA = np.mean(dataA, axis=0)
#            dataB = np.mean(dataB, axis=0)
        maxADC = 2**16-100
        minADC = 100
        maxA = np.max(dataA)
        maxB = np.max(dataB)
        minA = np.min(dataA)
        minB = np.min(dataB)
        if maxA > maxADC or maxB > maxADC or minA < minADC or minB < minADC :
            mes = '''Channel A or B are saturated: increase input range or
            decrease amplification'''
            raise InstrIOError(mes)
        return (dataA, dataB)

DRIVERS = {'Alazar935x': Alazar935x}
