from time import sleep
import pyfits
import numpy as np
import random
from controllercommon import *
import ctypes

class SimulatedCCDController:
    _lockOpen = False

    _rows = 4200
    _cols = 4200

    _controller_idling_flag = False
    _controller_master_flag = True
    _controller_power_flag = False

    _readout_rows = 0

    _default_dac_values = (-12, -12, -12, -12, 2.6, 2.6, 2.6, 2.6,
                           -23, -23, -23, -23, 0, 0, 0, 0, 50)
    _dac_values = list(_default_dac_values)

    _default_clock_values = ((6,-4),(6,-4),(6,-4),(-6,0),(6,-4),(6,-4),(6,-4),
                            (-6,0),(5,-3),(5,-3),(5,-3),(5,-3),(5,-3),(5,-3),
                            (5,-3),(5,-3),(5,-3),(5,-3),(5,-5),(5,-5))
    _clock_values = list(_default_clock_values)

    _default_offset_values = (-1.6,)*4 + (0,)*4
    _offset_values = list(_default_offset_values)


    _default_delay_values = {"clock_parallel": 2000, "clock_reset": 28, 
                    "clock_serial": 40, "clock_sumwell": 30,
                    "other1": 7, "other2": 7, "other3": 7, "other4": 7,
                    "settling_reset": 20, "settling_signal": 20}
    _delay_values = _default_delay_values.copy()

    _default_cds_values = {"averaging": 9, "digioff": 0, "nsamp_reset": 512,
                         "nsamp_signal": 512}
    _cds_values = _default_cds_values.copy()

    _enabled_dacs = [True]*len(_default_dac_values)
    _enabled_clks = [True]*len(_default_clock_values)

    _erase_vclk = 11.0
    _erase_vsub = 0.0
    _erase_slew = 100
    _erase_delay = 500

    _purge_vclk = -9.0
    _purge_delay = 500

    def _assertOpen(self, errorMessage):
        if not self._lockOpen:
            raise LBNLError(errorMessage  + ": don't have lock", FAILED)

    def aquireLock(self):
        if self._lockOpen:
            raise LBNLError("Couldn't aquire lock because lock already obtained")
        self._lockOpen = True

    #run this when you are done; removes lockfile
    def releaseLock(self):
        if self._lockOpen == False:
            raise LBNLError("Couldn't release lock: don't have lock")
        self._lockOpen = False

    #return true if you can use the library
    def checkLock(self):
        return self._lockOpen

    def init(self):
        self._assertOpen(" failed")
        sleep(1)

    def ccd_clear(self):
        self._assertOpen("CCD clear failed")
        sleep(2)

    def ccd_erase(self):
        self._assertOpen("CCD erase failed")
        sleep(1)

    def ccd_purge(self):
        self._assertOpen("CCD purge failed")
        sleep(1)

    def ccd_set_erase_params(self, vclk, vsub, slew, delay):
        self._assertOpen("Setting CCD erase parameters failed")
        self._erase_vclk = vclk
        self._erase_vsub = vsub
        self._erase_slew = slew
        self._erase_delay = delay
        sleep(.01)

    def ccd_get_erase_params(self):
        self._assertOpen("Getting CCD erase parameters failed")
        return (self._erase_vclk, self._erase_vsub, self._erase_slew, self._erase_delay)

    def ccd_set_purge_params(self, vclk, delay):
        self._assertOpen("Setting CCD purge parameters failed")
        self._purge_vclk = vclk
        self._purge_delay = delay

    def ccd_get_purge_params(self):
        self._assertOpen("Getting CCD purge parameters failed")
        return (self._purge_vclk, self._purge_delay)

    def ccd_read(self):
        self._assertOpen('CCD read failed')
        size = self._rows * self._cols
        data = (ctypes.c_ushort * size)()
        for i in range(size):
            data[i]= 32768
        self._readout_rows = 0
        rowsps = self._rows / 42
        for i in xrange(42):
            sleep(1)
            self._readout_rows += rowsps
        self._readout_rows = self._rows
        return data

    #simulated CCD read is indistinguishable from simulated simulated CCD read
    def ccd_read_sim(self):
        return self.ccd_read()

    def readout_prepare(self):
        self._assertOpen("preparing readout failed")
        sleep(4)

    def readout_discard(self):
        self._assertOpen("discarding readout failed")

    def ccd_set_size(self, r,c):
        self._assertOpen("setting CCD size failed")
        self._rows = r
        self._cols = c

    def ccd_get_size(self):
        self._assertOpen("getting CCD size failed")
        return (self._rows,self._cols)

    def ccd_idle(self, flag):
        self._controller_idling_flag = flag

    #TODO do does the header to be the same?
    def readout_get_fits(self, imageData, filename):
        self._assertOpen('Getting FITS failed')
        pyfits.PrimaryHDU(imageData).writeto(filename, clobber=True)

    def readout_get_status(self):
        self._assertOpen('Getting readout status failed')
        status_dict = {}
        status_dict['rows_read'] = self._readout_rows
        status_dict['progress'] = (100*self._readout_rows)/self._rows
        return status_dict

    def controller_get_status(self):
        self._assertOpen("couldn't get controller status")
        status_dict = {}
        status_dict['power_on'] = self._controller_power_flag
        status_dict['ccd_idle'] = self._controller_idling_flag
        status_dict['clk_mask'] = self._enabled_clks
        status_dict['dac_mask'] = self._enabled_dacs
        return status_dict

    def controller_upload_timing(self, filepath):
        self._assertOpen("Coudn't upload timing")
        sleep(.1)
        
    def controller_set_start_address(self, start_address):
        sleep(.1)

    def controller_power(self, flag):
        self._assertOpen("Couldn't set controller power")
        self._controller_power_flag = flag

    def controller_master(self, flag):
        self._assertOpen("Couldn't set controller master")
        self.controller_master_flag = flag

    def controller_enable(self, dac_bools, clk_bools):
        self._assertOpen("Couldn't enable controllers")
        self._enabled_dacs  = dac_bools
        self._enabled_clks = clk_bools

    def controller_set_gain(self, bools):
        self._assertOpen("Couldn't set gain")

    def controller_get_temps(self):
        self._assertOpen("Couldn't get controller temps")
        #TODO what should the mean be?
        return (random.gauss(80, 5), random.gauss(80,5))

    #TODO add raw_value, telemetry, and raw_telemetry to 
    #controller_get_all return types

    def controller_get_all_dacs(self):
        self._assertOpen("Failed getting all DAC values")
        dacs = []
        for i,d in enumerate(self._dac_values):
            dacs.append({'address': i, 'tvalue': d})
        return dacs

    def controller_get_ndacs(self):
        self._assertOpen("Couldn't get number of DACs")
        return len(self._dac_values)

    def controller_get_all_clocks(self):
        self._assertOpen("Failed getting all clock values")
        clks = []
        for i,(h,l) in enumerate(self._clock_values):
            clks.append({'address': i, 'tlow_values': l, 'thigh_value': h})
        return clks

    def controller_get_nclocks(self):
        self._assertOpen("Couldn't get number of clocks")
        return len(self._clock_values)

    def controller_get_all_offsets(self):
        self._assertOpen("Couldn't get number of offsets")
        offsets = []
        for i, o in enumerate(self._offset_values):
            offsets.append({'address': i, 'tvalue': o})
        return offsets

    def controller_get_noffsets(self):
        self._assertOpen("Couldn't get number of offsets")
        return len(self._offset_values)


    #engineering level functions

    def controller_set_dac_value(self, address, value):
        self._assertOpen("Couldn't set DAC value")
        self._dac_values[address] = value

    def controller_set_clk_value(self, address, high, low):
        self._assertOpen("Couldn't set clock value")
        self._clock_values[address] = (high, low)

    def controller_set_offset_value(self, address, value):
        self._assertOpen("Couldn't set offset value")
        self._offset_values[address] = value

    def controller_set_default_offsets(self):
        self._assertOpen("Couldn't set default offsets")
        self._offset_values = list(self._default_offset_values)

    def controller_set_delays(self, **delays):
        self._assertOpen("Couldn't set delays")
        for key, val in delays.iteritems():
            if key not in self._delay_values:
                raise LBNLError("%s is not a valid delay" % key)
            self._delay_values[key] = val

    def controller_set_default_delays(self):
        self._assertOpen("Couldn't set default delays")
        self._delay_values = self._default_delay_values.copy()
    
    def controller_get_delays(self):
        self._assertOpen("Couldn't get delays")
        return self._delay_values

    def controller_set_default_dacs(self):
        self._assertOpen("Couldn't set default DACs")
        self._dac_values = list(self._default_dac_values)

    def controller_set_default_clks(self):
        self._assertOpen("Couldn't set default clocks")
        self._clock_values = list(self._default_clock_values)

    def controller_set_cds(self, **cds):
        self._assertOpen("Couldn't set CDs")
        for key, val in cds.iteritems():
            if key not in self._cds_values:
                raise LBNLError("%s is an invalid CDS param" % key)
            self._cds_values[key] = val
        
    def controller_set_default_cds(self):
        self._assertOpen("Couldn't set default CDS")
        self._cds_values = self._default_cds_values.copy()
    
    def controller_get_cds(self):
        self._assertOpen("Can't get CDS")
        return self._cds_values

    def controller_read_register(self):
        return NotImplementedError()

    def controller_write_register(self):
        return NotImplementedError()
