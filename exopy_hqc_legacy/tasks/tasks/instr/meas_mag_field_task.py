"""Task to read a magnetic field.

"""
from time import sleep
import numbers

from atom.api import (Float, Value, Str, set_default)

from exopy.tasks.api import InstrumentTask, validators


class MeasMagFieldTask(InstrumentTask):
    """Measure an applied magnetic field.

    Wait for any parallel operation before execution and then wait the
    specified time before perfoming the measure.

    """
    # Time to wait before the measurement.
    wait_time = Float().tag(pref=True)

    database_entries = set_default({'field': 1.0})

    wait = set_default({'activated': True, 'wait': ['instr']})

    def perform(self):
        """Wait and read the magnetic field.

        """
        if hasattr(self.driver, 'read_field'):
            self.driver.setup_dc()
            sleep(self.wait_time)
            value = self.driver.read_field()
        else:
            sleep(self.wait_time)
            value = self.driver.persistent_field
        
        self.write_in_database('field', value)

class MeasACMagFieldTask(InstrumentTask):
    """Measure an applied AC magnetic field.

    Wait for any parallel operation before execution and then wait the
    specified time before perfoming the measure.

    """
    # Time to wait before the measurement.

    filter_switch = Str('No filter').tag(pref=True)

    filter_freq = Str('').tag(
                    pref=True, 
                    feval=validators.SkipLoop(types=numbers.Real)
                    )

    wait_time = Float().tag(pref=True)

    database_entries = set_default({'filter': 'No filter',
                                    'filter_freq':0.0,
                                    'ac_field': 1.0,
                                    'ac_freq': 1.0})

    wait = set_default({'activated': True, 'wait': ['instr']})

    def perform(self):
        """Wait and read the magnetic field.

        """
        filter_freq=self.format_and_eval_string(self.filter_freq)

        if self.filter_switch=='LP':
            self.driver.setup_ac(filter_freq,None)
            self.write_in_database('filter_freq', filter_freq)
        elif self.filter_switch=='WBP':
            self.driver.setup_ac(None,filter_freq)
            self.write_in_database('filter_freq', filter_freq)
        else:
            self.driver.setup_ac(None,None)
        
        self.write_in_database('filter', self.filter_switch)
        
        sleep(self.wait_time)

        field_value = self.driver.read_field()
        self.write_in_database('ac_field', field_value)

        if self.filter_switch!='No filter':
            freq_value = self.driver.read_freq()
            self.write_in_database('ac_freq', freq_value)
