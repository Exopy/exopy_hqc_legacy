# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by ExopyHqcLegacy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Configuration for the tests run on tasks.

"""
import pytest
import enaml

with enaml.imports():
    from exopy_hqc_legacy.manifest import HqcLegacyManifest

pytest_plugins = str('exopy.testing.tasks.fixtures'),


@pytest.yield_fixture
def task_workbench(task_workbench):
    """Task workbench in which the HqcLegacyManifest has been registered.

    """
    task_workbench.register(HqcLegacyManifest())
    yield task_workbench
    task_workbench.unregister('exopy_hqc_legacy')
