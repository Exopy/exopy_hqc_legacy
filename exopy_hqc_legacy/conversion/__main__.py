# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Start up script for HQCMeas .ini files to exopy converter tool.

"""
import sys

import enaml
from enaml.qt.qt_application import QtApplication

with enaml.imports():
    from .ui import Main


def main():
    """Start the GUI.

    """
    app = QtApplication()
    if sys.platform == 'win32':
        import ctypes
        myappid = 'exopy.hqcmeas_converter' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    win = Main()
    win.show()

    sys.exit(app.start())


if __name__ == '__main__':
    main()
