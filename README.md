Ecpy Hqc Legacy
===============

[![Build Status](https://travis-ci.org/Ecpy/ecpy_hqc_legacy.svg?branch=master)](https://travis-ci.org/Ecpy/ecpy_hqc_legacy)
[![Anaconda-Server Badge](https://anaconda.org/ecpy/ecpy_hqc_legacy/badges/version.svg)](https://anaconda.org/ecpy/ecpy_hqc_legacy)

Transition package to smooth transition from HQCMeas to Ecpy.

Installation
------------

conda install ecpy_hqc_legacy -c ecpy -c conda-forge

WORK IN PROGRESS

A GUI tool is provided to convert an HQCMeas measure file to the new format used
by Ecpy. It can be started from the command line by typing hqcmeas_to_ecpy.

FAQs
----

- Q: I want to add a driver to ecpy_hqc_legacy, so I referred to html/dev_guide/instruments.html#registering-a-driver but I cannot find the "plugin manifest".
- A: The plugin manifest is here: ecpy_hqc_legacy\ecpy_hqc_legacy\manifest.enaml

- Q: Why is my instrument not appearing in the list of proposed instrument for a chosen task?
- A: Go to ecpy_hqc_legacy\ecpy_hqc_legacy\manifest.enaml and add your instrument to the instruments list for the task you want: 
	 e.g. instruments = ['ecpy_hqc_legacy.Legacy.AgilentPNA','ecpy_hqc_legacy.Legacy.ZNB20']

- Q: I created a task file, but do not see it appear as the proposed tasks in the GUI, why?
- A: You need to add the task in the plugin manifest ecpy_hqc_legacy\ecpy_hqc_legacy\manifest.enaml
	 
