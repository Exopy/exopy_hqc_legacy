# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2017 by EcpyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task perform measurements with a synthHD.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Int

from ecpy.tasks.api import TaskInterface


class SynthHDsetChannelInterface(TaskInterface):
    """Set the central frequency to be used for the specified channel.

    """
    #: Id of the channel whose central frequency should be set.
    channel = Int(0).tag(pref=True)

    def perform(self, frequency=None):
        """Set the central frequency of the specified channel.

        """
        task = self.task
        channel = self.channel
        task.driver.channel = channel
        task.i_perform()

    def check(self, *args, **kwargs):
        """Make sure the specified channel does exists on the instrument.

        """
        test, traceback = super(SynthHDsetChannelInterface, self).check(*args,
                                                                      **kwargs)
        return test, traceback
