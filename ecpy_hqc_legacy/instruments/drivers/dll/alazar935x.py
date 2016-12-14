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
import numpy as np
import ctypes
from inspect import cleandoc
import matplotlib.pyplot as plt

from pyclibrary import CLibrary

from ..dll_tools import DllInstrument
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
        board.setCaptureClock(    ats.EXTERNAL_CLOCK, # ZL: changed from EXTERNAL_CLOCK_10MHz_REF
                                  ats.SAMPLE_RATE_500MSPS, # ZL: changed from 500000000
                                  ats.CLOCK_EDGE_RISING,
                                  1)
        # TODO: Select channel A input parameters as required.
        board.inputControl(    ats.CHANNEL_A,
                               ats.AC_COUPLING,
                               ats.INPUT_RANGE_PM_2_V,
                               ats.IMPEDANCE_50_OHM)

        # TODO: Select channel A bandwidth limit as required.
        board.setBWLimit(ats.CHANNEL_A, 0)


        # TODO: Select channel B input parameters as required.
        board.inputControl(ats.CHANNEL_B,
                               ats.AC_COUPLING,
                               ats.INPUT_RANGE_PM_2_V,
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

    def get_traces(self, timeaftertrig, recordsPerCapture,
                   recordsPerBuffer, average, verbose=False):

        if recordsPerCapture%recordsPerBuffer != 0:
            raise Exception("Error: Number of records per capture must be an integer times the number of records per buffer! (recordsPerCapture = %s,recordsPerBuffer = %s)" %
                            (recordsPerCapture,recordsPerBuffer))

        samplesPerSec = 500e6
        postTriggerSamples = int(samplesPerSec*timeaftertrig)
        if postTriggerSamples % 32 == 0:
            postTriggerSamples = int(postTriggerSamples)
        else:
            postTriggerSamples = int((postTriggerSamples)/32 + 1)*32

        board = self.board
        # No pre-trigger samples in NPT mode
        preTriggerSamples = 0

        # TODO: Select the number of samples per record.
        #postTriggerSamples = 2048

        # TODO: Select the number of records per DMA buffer.
        #recordsPerBuffer = 10

        # TODO: Select the number of buffers per acquisition.
        #buffersPerAcquisition = 10
        buffersPerAcquisition = int(math.ceil(recordsPerCapture / recordsPerBuffer))

        # TODO: Select the active channels.
        channels = ats.CHANNEL_A | ats.CHANNEL_B
        channelCount = 0
        for c in ats.channels:
            channelCount += (c & channels == c)

        # TODO: Should data be saved to file?
        saveData = False
        dataFile = None
        if saveData:
            dataFile = open(os.path.join(os.path.dirname(__file__), "NPT_data.bin"), 'w')

        # Compute the number of bytes per record and per buffer
        memorySize_samples, bitsPerSample = board.getChannelInfo()
        bytesPerSample = (bitsPerSample.value + 7) // 8
        samplesPerRecord = preTriggerSamples + postTriggerSamples
        bytesPerRecord = bytesPerSample * samplesPerRecord
        bytesPerBuffer = bytesPerRecord * recordsPerBuffer * channelCount

        # TODO: Select number of DMA buffers to allocate
        bufferCount = 4

        # Allocate DMA buffers
        buffers = []
        for i in range(bufferCount):
            buffers.append(ats.DMABuffer(bytesPerSample, bytesPerBuffer))

        # Set the record size
        board.setRecordSize(preTriggerSamples, postTriggerSamples)

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
        if verbose: print("Capturing %d buffers. Press any key to abort" % buffersPerAcquisition)
        buffersCompleted = 0
        bytesTransferred = 0

        dataA = np.empty((recordsPerCapture, samplesPerRecord))
        dataB = np.empty((recordsPerCapture, samplesPerRecord))

        if verbose: fig, ax = plt.subplots()
        while buffersCompleted < buffersPerAcquisition:
            # Wait for the buffer at the head of the list of available
            # buffers to be filled by the board.
            buffer = buffers[buffersCompleted % len(buffers)]
            board.waitAsyncBufferComplete(buffer.addr, timeout_ms=5000)
            data = np.reshape(buffer.buffer, (recordsPerBuffer*channelCount, -1))
            dataA[buffersCompleted*recordsPerBuffer:(buffersCompleted+1)*recordsPerBuffer] = data[:recordsPerBuffer]
            dataB[buffersCompleted*recordsPerBuffer:(buffersCompleted+1)*recordsPerBuffer] = data[recordsPerBuffer:]

            buffersCompleted += 1
            bytesTransferred += buffer.size_bytes

            # TODO: Process sample data in this buffer. Data is available
            # as a NumPy array at buffer.buffer

            # NOTE:
            #
            # While you are processing this buffer, the board is already
            # filling the next available buffer(s).
            #
            # You MUST finish processing this buffer and post it back to the
            # board before the board fills all of its available DMA buffers
            # and on-board memory.
            #
            # Records are arranged in the buffer as follows:
            # R0A, R1A, R2A ... RnA, R0B, R1B, R2B ...
            #
            # A 12-bit sample code is stored in the most significant bits of
            # in each 16-bit sample value.
            #
            # Sample codes are unsigned by default. As a result:
            # - a sample code of 0x0000 represents a negative full scale input signal.
            # - a sample code of 0x8000 represents a ~0V signal.
            # - a sample code of 0xFFFF represents a positive full scale input signal.
            # Optionaly save data to file

            if verbose: ax.plot(buffer.buffer)
            if dataFile: buffer.buffer.tofile(dataFile)

            # Update progress bar

            # Add the buffer to the end of the list of available buffers.
            board.postAsyncBuffer(buffer.addr, buffer.size_bytes)
        # Compute the total transfer time, and display performance information.
        transferTime_sec = time.clock() - start
        if verbose: print("Capture completed in %f sec" % transferTime_sec)
        buffersPerSec = 0
        bytesPerSec = 0
        recordsPerSec = 0
        if transferTime_sec > 0:
            buffersPerSec = buffersCompleted / transferTime_sec
            bytesPerSec = bytesTransferred / transferTime_sec
            recordsPerSec = recordsPerBuffer * buffersCompleted / transferTime_sec
        if verbose:
            print("Captured %d buffers (%f buffers per sec)" % (buffersCompleted, buffersPerSec))
            print("Captured %d records (%f records per sec)" % (recordsPerBuffer * buffersCompleted, recordsPerSec))
            print("Transferred %d bytes (%f bytes per sec)" % (bytesTransferred, bytesPerSec))

        # Abort transfer.
        board.abortAsyncRead()

        # Re-shaping of the data for demodulation and demodulation
        dataA = dataA[:,1:samplesPerRecord + 1]
        dataB = dataB[:,1:samplesPerRecord + 1]

                # Averaging if needed and converting binary numbers into Volts
        if average:
            dataA = np.mean(dataA, axis=0)
            dataB = np.mean(dataB, axis=0)

        return (dataA, dataB)

DRIVERS = {'Alazar935x': Alazar935x}
