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
import atsapi as ats

from pyclibrary import CLibrary

from ..dll_tools import DllInstrument

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
        self._dll = CLibrary('ATSApi.dll', headers,
                             cache=cache_path, prefix=['Alazar'],
                             convention='windll')

    def open_connection(self):
        """Do not need to open a connection

        """
        pass

    def close_connection(self):
        """Do not need to close a connection

        """
        pass

    def configure_board(self):
        board = ats.Board(systemId = 1, boardId = 1)
        # TODO: Select clock parameters as required to generate this
        # sample rate
        global samplesPerSec
        samplesPerSec = 500000000.0
        board.setCaptureClock(ats.EXTERNAL_CLOCK,
                              ats.SAMPLE_RATE_500MSPS,
                              ats.CLOCK_EDGE_RISING,
                              0)

        # TODO: Select channel A input parameters as required.
        board.inputControl(ats.CHANNEL_A,
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
        triggerDelay_samples = int(triggerDelay_sec * samplesPerSec + 0.5)
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
        board.setTriggerTimeOut(triggerTimeout_clocks)

        # Configure AUX I/O connector as required
        board.configureAuxIO(ats.AUX_OUT_TRIGGER,
                             0)

    def get_demod(self, startaftertrig, duration, recordsPerCapture,
                  recordsPerBuffer, timestep, freq, average, NdemodA, NdemodB, NtraceA, NtraceB):

        board = self._dll.GetBoardBySystemID(1, 1)()

        # Number of samples per record: must be divisible by 32
        samplesPerSec = 500000000.0
        samplesPerTrace = int(samplesPerSec * np.max(np.array(startaftertrig) + np.array(duration)))
        if samplesPerTrace % 32 == 0:
            samplesPerRecord = int(samplesPerTrace)
        else:
            samplesPerRecord = int((samplesPerTrace)/32 + 1)*32

        retCode = self._dll.GetChannelInfo(board)()
        bitsPerSample = self._dll.GetChannelInfo(board)[1]
        if retCode != self._dll.ApiSuccess:
            raise ValueError(cleandoc(self._dll.AlazarErrorToText(retCode)))

        # Compute the number of bytes per record and per buffer
        channel_number = 2 if ((NdemodA or NtraceA) and (NdemodB or NtraceB)) else 1  # Acquisition on A and B
        ret, (boardhandle, memorySize_samples,
              bitsPerSample) = self._dll.GetChannelInfo(board)
        bytesPerSample = (bitsPerSample + 7) // 8
        bytesPerRecord = bytesPerSample * samplesPerRecord
        bytesPerBuffer = int(bytesPerRecord * recordsPerBuffer*channel_number)

        # For converting data into volts
        channelRange = 0.4 # Volts
        bitsPerSample = 12
        bitShift = 4
        code = (1 << (bitsPerSample - 1)) - 0.5

        bufferCount = int(round(recordsPerCapture / recordsPerBuffer))
        buffers = []
        for i in range(bufferCount):
            buffers.append(DMABuffer(bytesPerSample, bytesPerBuffer))

        # Set the record size
        self._dll.SetRecordSize(board, 0, samplesPerRecord)

        # Configure the number of records in the acquisition
        acquisition_timeout_sec = 10
        self._dll.SetRecordCount(board, int(recordsPerCapture))

        # Calculate the number of buffers in the acquisition
        buffersPerAcquisition = round(recordsPerCapture / recordsPerBuffer)

        channelSelect = 1 if not (NdemodB or NtraceB) else (2 if not (NdemodA or NtraceA) else 3)
        self._dll.BeforeAsyncRead(board, channelSelect,  # Channels A & B
                                  0,
                                  samplesPerRecord,
                                  int(recordsPerBuffer),
                                  int(recordsPerCapture),
                                  self._dll.ADMA_EXTERNAL_STARTCAPTURE |
                                  self._dll.ADMA_NPT)()

        # Post DMA buffers to board. ATTENTION it is very important not to do "for buffer in buffers"
        for i in range(bufferCount):
            buffer = buffers[i]
            self._dll.PostAsyncBuffer(board, buffer.addr, buffer.size_bytes)

        start = time.clock()  # Keep track of when acquisition started
        self._dll.StartCapture(board)  # Start the acquisition

        if time.clock() - start > acquisition_timeout_sec:
            self._dll.AbortCapture()
            raise Exception("Error: Capture timeout. Verify trigger")
            time.sleep(10e-3)

        # Preparation of the tables for the demodulation

        startSample = []
        samplesPerDemod = []
        samplesPerBlock = []
        NumberOfBlocks = []
        samplesMissing = []
        data = []
        dataExtended = []

        for i in range(NdemodA + NdemodB):
            startSample.append( int(samplesPerSec * startaftertrig[i]) )
            samplesPerDemod.append( int(samplesPerSec * duration[i]) )

            if timestep[i]:
                samplesPerBlock.append( samplesPerDemod[i] )
            else:
                # Check wheter it is possible to cut each record in blocks of size equal
                # to an integer number of periods
                periodsPerBlock = 1
                while (periodsPerBlock * samplesPerSec < freq[i] * samplesPerDemod[i]
                       and periodsPerBlock * samplesPerSec % freq[i]):
                    periodsPerBlock += 1
                samplesPerBlock.append( int(np.minimum(periodsPerBlock * samplesPerSec / freq[i],
                                                      samplesPerDemod[i])) )

            NumberOfBlocks.append( np.divide(samplesPerDemod[i], samplesPerBlock[i]) )
            samplesMissing.append( (-samplesPerDemod[i]) % samplesPerBlock[i] )
            # Makes the table that will contain the data
            data.append( np.empty((recordsPerCapture, samplesPerBlock[i])) )
            dataExtended.append( np.zeros((recordsPerBuffer, samplesPerDemod[i] + samplesMissing[i]),
                                          dtype='uint16') )

        for i in (np.arange(NtraceA + NtraceB) + NdemodA + NdemodB):
            startSample.append( int(samplesPerSec * startaftertrig[i]) )
            samplesPerDemod.append( int(samplesPerSec * duration[i]) )
            data.append( np.empty((recordsPerCapture, samplesPerDemod[i])) )

        start = time.clock()

        buffersCompleted = 0
        while buffersCompleted < buffersPerAcquisition:

            # Wait for the buffer at the head of the list of available
            # buffers to be filled by the board.
            buffer = buffers[buffersCompleted % len(buffers)]
            self._dll.WaitAsyncBufferComplete(board, buffer.addr, 10000)

            # Process data

            dataRaw = np.reshape(buffer.buffer, (recordsPerBuffer*channel_number, -1))
            dataRaw = dataRaw >> bitShift

            for i in np.arange(NdemodA):
                dataExtended[i][:,:samplesPerDemod[i]] = dataRaw[:recordsPerBuffer,startSample[i]:startSample[i]+samplesPerDemod[i]]
                dataBlock = np.reshape(dataExtended[i],(recordsPerBuffer,-1,samplesPerBlock[i]))
                data[i][buffersCompleted*recordsPerBuffer:(buffersCompleted+1)*recordsPerBuffer] = np.sum(dataBlock, axis=1)

            for i in (np.arange(NdemodB) + NdemodA):
                dataExtended[i][:,:samplesPerDemod[i]] = dataRaw[(channel_number-1)*recordsPerBuffer:channel_number*recordsPerBuffer,startSample[i]:startSample[i]+samplesPerDemod[i]]
                dataBlock = np.reshape(dataExtended[i],(recordsPerBuffer,-1,samplesPerBlock[i]))
                data[i][buffersCompleted*recordsPerBuffer:(buffersCompleted+1)*recordsPerBuffer] = np.sum(dataBlock, axis=1)

            for i in (np.arange(NtraceA) + NdemodB + NdemodA):
                data[i][buffersCompleted*recordsPerBuffer:(buffersCompleted+1)*recordsPerBuffer] = dataRaw[:recordsPerBuffer,startSample[i]:startSample[i]+samplesPerDemod[i]]

            for i in (np.arange(NtraceB) + NtraceA + NdemodB + NdemodA):
                data[i][buffersCompleted*recordsPerBuffer:(buffersCompleted+1)*recordsPerBuffer] = dataRaw[(channel_number-1)*recordsPerBuffer:channel_number*recordsPerBuffer,startSample[i]:startSample[i]+samplesPerDemod[i]]

            buffersCompleted += 1

            self._dll.PostAsyncBuffer(board, buffer.addr, buffer.size_bytes)

        self._dll.AbortAsyncRead(board)

        for i in range(bufferCount):
            buffer = buffers[i]
            buffer.__exit__()

        print time.clock() - start

        # Normalize the np.sum and convert data into Volts
        for i in range(NdemodA + NdemodB):
            normalisation = 1 if samplesMissing[i] else 0
            data[i][:,:samplesPerBlock[i]-samplesMissing[i]] /= NumberOfBlocks[i] + normalisation
            data[i][:,samplesPerBlock[i]-samplesMissing[i]:] /= NumberOfBlocks[i]
            data[i] = (data[i] / code - 1) * channelRange
        for i in (np.arange(NtraceA + NtraceB) + NdemodA + NdemodB):
            data[i] = (data[i] / code - 1) * channelRange

        # calculate demodulation tables
        coses=[]
        sines=[]
        for i in range(NdemodA+NdemodB):
            dem = np.arange(samplesPerBlock[i])
            coses.append(np.cos(2. * math.pi * dem * freq[i] / samplesPerSec))
            sines.append(np.sin(2. * math.pi * dem * freq[i] / samplesPerSec))

        # prepare the structure of the answered array

        if (NdemodA or NdemodB):
            answerTypeDemod = []
            zerosDemodA = 1 + int(np.floor(np.log10(NdemodA))) if NdemodA else 0
            zerosDemodB = 1 + int(np.floor(np.log10(NdemodB))) if NdemodB else 0
            for i in range(NdemodA):
                answerTypeDemod += [('AI' + str(i).zfill(zerosDemodA), str(data[0].dtype)),
                                    ('AQ' + str(i).zfill(zerosDemodA), str(data[0].dtype))]
            for i in range(NdemodB):
                answerTypeDemod += [('BI' + str(i).zfill(zerosDemodB), str(data[0].dtype)),
                                    ('BQ' + str(i).zfill(zerosDemodB), str(data[0].dtype))]
            lengthDemod = [(samplesPerDemod[i]/int(samplesPerSec*timestep[i]) if timestep[i] else 1) for i in range(NdemodA+NdemodB)]
            biggerDemod = max(lengthDemod)
        else:
            answerTypeDemod = 'f'
            biggerDemod = 0

        if (NtraceA or NtraceB):
            zerosTraceA = 1 + int(np.floor(np.log10(NtraceA))) if NtraceA else 0
            zerosTraceB = 1 + int(np.floor(np.log10(NtraceB))) if NtraceB else 0
            answerTypeTrace = ( [('A' + str(i).zfill(zerosTraceA), str(data[0].dtype)) for i in range(NtraceA)]
                              + [('B' + str(i).zfill(zerosTraceB), str(data[0].dtype)) for i in range(NtraceB)] )
            biggerTrace = np.max(samplesPerDemod[NdemodA+NdemodB:])
        else:
            answerTypeTrace = 'f'
            biggerTrace = 0

        if average:
            answerDemod = np.zeros(biggerDemod, dtype=answerTypeDemod)
            answerTrace = np.zeros(biggerTrace, dtype=answerTypeTrace)
        else:
            answerDemod = np.zeros((recordsPerCapture, biggerDemod), dtype=answerTypeDemod)
            answerTrace = np.zeros((recordsPerCapture, biggerTrace), dtype=answerTypeTrace)

        # Demodulate the data, average them if asked and return the result

        for i in np.arange(NdemodA+NdemodB):
            if i<NdemodA:
                Istring = 'AI' + str(i).zfill(zerosDemodA)
                Qstring = 'AQ' + str(i).zfill(zerosDemodA)
            else:
                Istring = 'BI' + str(i-NdemodA).zfill(zerosDemodB)
                Qstring = 'BQ' + str(i-NdemodA).zfill(zerosDemodB)
            angle = 2 * np.pi * freq[i] * startSample[i] / samplesPerSec
            if average:
                data[i] = np.mean(data[i], axis=0)
                ansI = 2 * np.mean((data[i]*coses[i]).reshape(lengthDemod[i], -1), axis=1)
                ansQ = 2 * np.mean((data[i]*sines[i]).reshape(lengthDemod[i], -1), axis=1)
                answerDemod[Istring][:lengthDemod[i]] = ansI * np.cos(angle) - ansQ * np.sin(angle)
                answerDemod[Qstring][:lengthDemod[i]] = ansI * np.sin(angle) + ansQ * np.cos(angle)
            else:
                ansI = 2 * np.mean((data[i]*coses[i]).reshape(recordsPerCapture, lengthDemod[i], -1), axis=2)
                ansQ = 2 * np.mean((data[i]*sines[i]).reshape(recordsPerCapture, lengthDemod[i], -1), axis=2)
                answerDemod[Istring][:,:lengthDemod[i]] = ansI * np.cos(angle) - ansQ * np.sin(angle)
                answerDemod[Qstring][:,:lengthDemod[i]] = ansI * np.sin(angle) + ansQ * np.cos(angle)

        for i in (np.arange(NtraceA+NtraceB) + NdemodB+NdemodA):
            if i<NdemodA+NdemodB+NtraceA:
                Tracestring = 'A' + str(i-NdemodA-NdemodB).zfill(zerosTraceA)
            else:
                Tracestring = 'B' + str(i-NdemodA-NdemodB-NtraceA).zfill(zerosTraceB)
            if average:
                answerTrace[Tracestring][:samplesPerDemod[i]] = np.mean(data[i], axis=0)
            else:
                answerTrace[Tracestring][:,:samplesPerDemod[i]] = data[i]

        return answerDemod, answerTrace

    def get_traces(self, timeaftertrig, recordsPerCapture,
                   recordsPerBuffer, average):
        ''' timeaftertrig is in seconds!!!
        '''
        board = ats.Board(systemId = 1, boardId = 1)
        # TODO: Select the number of pre-trigger samples
        preTriggerSamples = 0

        # TODO: Select the number of samples per record.
        samplesPerSec = 500e6
        postTriggerSamples = int(samplesPerSec*timeaftertrig)

        # TODO: Select the amount of time to wait for the acquisition to
        # complete to on-board memory.
        acquisition_timeout_sec = 10

        # TODO: Select the active channels.
        channels = ats.CHANNEL_A | ats.CHANNEL_B
        channelCount = 0
        for c in ats.channels:
            channelCount += (c & channels == c)

        # Compute the number of bytes per record and per buffer
        memorySize_samples, bitsPerSample = board.getChannelInfo()
        print('bitsPerSample   '+str(bitsPerSample))
        bytesPerSample = (bitsPerSample.value + 7) // 8
        samplesPerRecord = preTriggerSamples + postTriggerSamples
        bytesPerRecord = bytesPerSample * samplesPerRecord

        # Calculate the size of a record buffer in bytes. Note that the
        # buffer must be at least 16 bytes larger than the transfer size.
        bytesPerBuffer = bytesPerSample * (samplesPerRecord*recordsPerBuffer*channelCount + 16)

        # Set the record size
        board.setRecordSize(preTriggerSamples, postTriggerSamples)

        # Configure the number of records in the acquisition
        board.setRecordCount(recordsPerCapture)

        start = time.clock() # Keep track of when acquisition started
        board.startCapture() # Start the acquisition
        print("Capturing %d record. Press any key to abort" % recordsPerCapture)
        buffersCompleted = 0
        bytesTransferred = 0

        if time.clock() - start > acquisition_timeout_sec:
            board.abortCapture()
            raise Exception("Error: Capture timeout. Verify trigger")
        time.sleep(10e-3)

        captureTime_sec = time.clock() - start
        recordsPerSec = 0
        if captureTime_sec > 0:
            recordsPerSec = recordsPerCapture / captureTime_sec
        print("Captured %d records in %f rec (%f records/sec)" % (recordsPerCapture, captureTime_sec, recordsPerSec))

        buffer = ats.DMABuffer(bytesPerSample, bytesPerBuffer)

        # Transfer the records from )won-board memory to our buffer
        print("Transferring %d records..." % recordsPerCapture)

        for record in range(recordsPerCapture):
            for channel in range(channelCount):
                channelId = ats.channels[channel]
                if channelId & channels == 0:
                    continue
                board.read(channelId,             # Channel identifier
                           buffer.addr,           # Memory address of buffer
                           bytesPerSample,        # Bytes per sample
                           record + 1,            # Record (1-indexed)
                           preTriggerSamples,     # Pre-trigger samples
                           samplesPerRecord)      # Samples per record
                bytesTransferred += bytesPerRecord;

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

        # Compute the total transfer time, and display performance information.
        transferTime_sec = time.clock() - start
        bytesPerSec = 0
        if transferTime_sec > 0:
            bytesPerSec = bytesTransferred / transferTime_sec
        print("Transferred %d bytes (%f bytes per sec)" % (bytesTransferred, bytesPerSec))
        return buffer.buffer


DRIVERS = {'Alazar935x': Alazar935x}
