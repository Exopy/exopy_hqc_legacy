Exopy Hqc Legacy
===============

.. image:: https://travis-ci.org/Exopy/exopy_hqc_legacy.svg?branch=master
    :target: https://travis-ci.org/Exopy/exopy_hqc_legacy
    :alt: Build Status
.. image:: https://anaconda.org/exopy/exopy_hqc_legacy/badges/version.svg
    :target: https://anaconda.org/exopy/exopy_hqc_legacy
    :alt: Conda package

Transition package to smooth transition from HQCMeas to Exopy.
A GUI tool is provided to convert an HQCMeas measure file to the new format
used by Exopy. It can be started from the command line by typing
hqcmeas_to_exopy.

Installation
------------

.. code:: shell

    conda install exopy_hqc_legacy -c exopy -c conda-forge

FAQs
----

- Q: I want to add a driver to exopy_hqc_legacy, so I referred to html/dev_guide/instruments.html#registering-a-driver but I cannot find the "plugin manifest".
- A: The plugin manifest is here: exopy_hqc_legacy\exopy_hqc_legacy\manifest.enaml

- Q: Why is my instrument not appearing in the list of proposed instrument for a chosen task?
- A: Go to exopy_hqc_legacy\exopy_hqc_legacy\manifest.enaml and add your instrument to the instruments list for the task you want:
	 e.g. instruments = ['exopy_hqc_legacy.Legacy.AgilentPNA','exopy_hqc_legacy.Legacy.ZNB20']

- Q: I created a task file, but do not see it appear as the proposed tasks in the GUI, why?
- A: You need to add the task in the plugin manifest exopy_hqc_legacy\exopy_hqc_legacy\manifest.enaml

