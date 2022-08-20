# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2022 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Driver for the Danfysik electromagnet power supplies.

"""
from inspect import cleandoc
from time import sleep
import logging

from ..driver_tools import (InstrIOError, secure_communication,
                            instrument_property, InstrJob)
from ..visa_tools import VisaInstrument

class Danfysik9100(VisaInstrument):
    """Driver for the electromagnet power supply danfysik 9100.

    """

    caching_permissions = {'target_field': True}

    log_prefix = 'Danfysik 9100 Driver: '

    baudrate = 9600
    flowcontrol = 0
    parity = 0
    databits = 8
    stopbits = 10
    maxcurr = 50.0

    def __init__(self, connection_info, caching_allowed=True,
                 caching_permissions={}, auto_open=True):
        super(Danfysik9100,self).__init__(connection_info,
                                    caching_allowed,
                                    caching_permissions,
                                    auto_open)
        log = logging.getLogger(__name__)
        msg = ('Init with parameters {}')
        log.info(self.log_prefix+msg.format(str(connection_info)))    
        try:
            br = connection_info['baudrate']
            self.set_baudrate(int(br))
            fc = connection_info['flowcontrol']
            self.set_flowcontrol(int(fc))
            pr = connection_info['parity']
            self.set_parity(int(pr))
            db = connection_info['databits']
            self.set_databits(int(db))
            sb = connection_info['stopbits']
            self.set_stopbits(int(sb))
            maxc = connection_info['maxcurr']
            self.set_maxcurr(float(maxc))            
        except KeyError:
            raise InstrIOError(cleandoc('''All connection parameters need to 
                                be specified in instrument settings panel 
                                to ensure smooth connection'''))
        self.update_connection_parameters()


    def set_baudrate(self,value):
        self.baudrate = value

    def set_flowcontrol(self,value):
        self.flowcontrol = value

    def set_parity(self,value):
        self.parity = value

    def set_databits(self,value):
        self.databits = value

    def set_stopbits(self,value):
        self.stopbits = value

    def set_maxcurr(self,value):
        self.maxcurr = value       

    def open_connection(self,**para):
        """Open the connection and set up the parameters.

        """
        super(Danfysik9100, self).open_connection()
        self.write_termination = '\r'
        self.read_termination = '\r\n'

    def reopen_connection(self,**para):
        """Open the connection and set up the parameters.

        """
        self.update_connection_parameters()

    def check_connection(self):
        try:
            status_byte = self.query('S1')
        except InstrIOError:
            raise ValueError('The status byte cannot be read')
        if status_byte == '.!...!..................':
            return True
        else:
            return False

    def update_connection_parameters(self):
        super(Danfysik9100, self).close_connection()
        super(Danfysik9100, self).open_connection(baud_rate=self.baudrate,
                                                  flow_control=self.flowcontrol,
                                                  parity=self.parity,
                                                  data_bits=self.databits,
                                                  stop_bits=self.stopbits)

    @instrument_property
    @secure_communication()
    def output_current(self):
        """Current that the source will try to reach.

        """
        # communicated in mA, returned in A
        value_string = self.query('RA').replace('\r', '').replace('\n', '')
        log = logging.getLogger(__name__)
        msg = ('Read current target (part of instr prop): {} mA')
        log.info(self.log_prefix+msg.format(value_string))
        sign_string = self.query('PO').replace('\r', '').replace('\n', '')
        log = logging.getLogger(__name__)
        msg = ('Polarity status is (part of instr prop): ')
        log.info(self.log_prefix+msg+sign_string)
        if sign_string == '-':
            sign=-1.0
        elif sign_string == '+':
            sign=1.0
        else:
            raise(InstrIOError(cleandoc(''' Power current source did not 
                                            return a proper sign''')))
        if value_string:
            value=float(value_string)/1000
            return sign*value
        else:
            raise(InstrIOError(cleandoc(''' Power current source did not 
                                            return a proper set value''')))

    @output_current.setter
    @secure_communication()
    def output_current(self, target):
        """Setter for the current that the source will try to reach.

        """
        # communicated in mA, asked in A
        if (abs(target)>self.maxcurr):
            raise(ValueError(cleandoc(''' Max allowed current by connection 
                                          info prevents this value ''')))
        log = logging.getLogger(__name__)
        msg = ('Setting current target (instr prop) : {} A')
        log.info(self.log_prefix+msg.format(target))
        current_string=str(int(target*1000))
        self.write('DA 0 {}'.format(current_string))
