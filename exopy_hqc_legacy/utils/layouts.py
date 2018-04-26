# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by EcpyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Layout function used for instrument task views.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from enaml.layout.api import grid


def auto_grid_layout(self):
    """Automatic layout =ing function for instrument tasks views.

    """
    children = self.widgets()
    labels = children[::2]
    widgets = children[1::2]
    n_labels = len(labels)
    n_widgets = len(widgets)
    if n_labels != n_widgets:
        if n_labels > n_widgets:
            labels.pop()
        else:
            widgets.pop()

    return [grid(labels, widgets)]
