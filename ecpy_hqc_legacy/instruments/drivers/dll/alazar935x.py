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
import math
from subprocess import call

import numpy as np

from ..dll_tools import DllInstrument
from ..driver_tools import InstrIOError
import atsapi as ats


class Alazar935x(DllInstrument):

    library = 'ATSApi.dll'

    def __init__(self, connection_infos, caching_allowed=True,
                 caching_permissions={}, auto_open=True):

        super(Alazar935x, self).__init__(connection_infos, caching_allowed,
                                         caching_permissions, auto_open)

        if auto_open:
            self.open_connection()

    def open_connection(self):
        """Do not need to open a connection

        """
        try:
            call("TASKKILL /F /IM AlazarDSO.exe", shell=True)
        except Exception:
            pass
        self.board = ats.Board()

    def close_connection(self):
        """Do not need to close a connection

        """
        pass

    def configure_board(self):
        """
        """
        board = self.board
        self.samplesPerSec = 500000000
        board.setCaptureClock(ats.EXTERNAL_CLOCK_10MHz_REF,
                              self.samplesPerSec,
                              ats.CLOCK_EDGE_RISING,
                              1)

        board.inputControl(ats.CHANNEL_A,
                           ats.AC_COUPLING,
                           ats.INPUT_RANGE_PM_100_MV,
                           ats.IMPEDANCE_50_OHM)

        board.setBWLimit(ats.CHANNEL_A, 0)

        board.inputControl(ats.CHANNEL_B,
                           ats.AC_COUPLING,
                           ats.INPUT_RANGE_PM_40_MV,
                           ats.IMPEDANCE_50_OHM)

        board.setBWLimit(ats.CHANNEL_B, 0)

        board.setTriggerOperation(ats.TRIG_ENGINE_OP_J,
                                  ats.TRIG_ENGINE_J,
                                  ats.TRIG_EXTERNAL,
                                  ats.TRIGGER_SLOPE_POSITIVE,
                                  150,
                                  ats.TRIG_ENGINE_K,
                                  ats.TRIG_DISABLE,
                                  ats.TRIGGER_SLOPE_POSITIVE,
                                  128)

        board.setExternalTrigger(ats.DC_COUPLING, ats.ETR_5V)

        triggerDelay_sec = 0.
        triggerDelay_samples = int(triggerDelay_sec * self.samplesPerSec + 0.5)
        board.setTriggerDelay(triggerDelay_samples)

        board.setTriggerTimeOut(0)

        board.configureAuxIO(ats.AUX_OUT_TRIGGER,
                             0)

    def get_traces(self, channels, duration, delay, records_per_capture,
                   retry=True, average=0):

        board = self.board
        timeaftertrig = duration
        recordsPerCapture = records_per_capture

        # both channels are always acquired
        channels = ats.CHANNEL_A | ats.CHANNEL_B
        channelCount = 0
        for c in ats.channels:
            channelCount += (c & channels == c)

        postTriggerSamples = int(self.samplesPerSec*timeaftertrig)
        if postTriggerSamples % 32 == 0:
            postTriggerSamples = int(postTriggerSamples)
        else:
            postTriggerSamples = int((postTriggerSamples)/32 + 1)*32
        # determine the number of records per buffer
        memorySize_samples, bitsPerSample = board.getChannelInfo()

        # No pre-trigger samples in NPT mode
        preTriggerSamples = 0
        bytesPerSample = (bitsPerSample.value + 7) // 8
        samplesPerRecord = preTriggerSamples + postTriggerSamples
        bytesPerRecord = bytesPerSample * samplesPerRecord

        # See remark page 93 in ATS-SDK-Guide 7.1.4
        # + following email exchange with Alazar
        # engineer Romain Deterre
        bytesPerBufferMax = 1e6
        rPB = int(math.floor(bytesPerBufferMax /
                  (bytesPerRecord * channelCount)))
        recordsPerBuffer = np.min([rPB, recordsPerCapture])
        bytesPerBuffer = bytesPerRecord * recordsPerBuffer * channelCount

        buffersPerAcquisition = int(math.ceil(float(recordsPerCapture) /
                                              recordsPerBuffer))
        records_to_ignore = buffersPerAcquisition*recordsPerBuffer \
            - recordsPerCapture

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

        board.startCapture()  # Start the acquisition
        buffersCompleted = 0
        bytesTransferred = 0

        dataA = np.empty((recordsPerCapture, samplesPerRecord))
        dataB = np.empty((recordsPerCapture, samplesPerRecord))

        while buffersCompleted < buffersPerAcquisition:

            # Wait for the buffer at the head of the list of available
            # buffers to be filled by the board.
            buffer = buffers[buffersCompleted % len(buffers)]
            board.waitAsyncBufferComplete(buffer.addr, timeout_ms=5000)
            data = np.reshape(buffer.buffer,
                              (recordsPerBuffer*channelCount, -1))

            # making sure we only grab the number of records we asked for
            if buffersCompleted < buffersPerAcquisition-1:
                records_to_ignore_val = 0
            else:
                records_to_ignore_val = records_to_ignore
            dataA[buffersCompleted*recordsPerBuffer: \
                (buffersCompleted+1)*recordsPerBuffer-records_to_ignore_val] \
                = data[:recordsPerBuffer-records_to_ignore_val]
            dataB[buffersCompleted*recordsPerBuffer: \
                (buffersCompleted+1)*recordsPerBuffer-records_to_ignore_val] \
                = data[recordsPerBuffer:2*recordsPerBuffer-records_to_ignore_val]

            buffersCompleted += 1
            bytesTransferred += buffer.size_bytes

            # Update progress bar

            # Add the buffer to the end of the list of available buffers.
            board.postAsyncBuffer(buffer.addr, buffer.size_bytes)

        # Abort transfer.
        board.abortAsyncRead()

        # Check card is not saturated
        maxADC = 2**16-100
        minADC = 100
        maxA = np.max(dataA)
        maxB = np.max(dataB)
        minA = np.min(dataA)
        minB = np.min(dataB)
        if maxA > maxADC or maxB > maxADC or minA < minADC or minB < minADC:
            mes = '''Channel A or B are saturated: increase input range or
            decrease amplification'''
            raise InstrIOError(mes)
        return (dataA, dataB)
