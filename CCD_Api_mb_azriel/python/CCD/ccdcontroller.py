from ctypes import *
from time import sleep
from controllercommon import *

SHARED_LIB_LOCATION = "/home/freddy/libccd/libCCD.so"

class DELAYS(Structure):
    _fields_ = [('settling_signal', c_ushort),
                ('settling_reset', c_ushort),
                ('clock_serial', c_ushort),
                ('clock_sumwell', c_ushort),
                ('clock_reset', c_ushort),
                ('clock_parallel', c_ushort),
                ('other1', c_ushort),
                ('other2', c_ushort),
                ('other3', c_ushort),
                ('other4', c_ushort)]

class CDS(Structure):
    _fields_ = [('nsamp_signal', c_ushort),
                ('nsamp_reset', c_ushort),
                ('averaging', c_ushort),
                ('digioff', c_ushort)]

class CCDController:
    def __init__(self):
        self.l = CDLL(SHARED_LIB_LOCATION)
        self.fd = 0

    def _boolToi8(self, b):
        if b: 
            return c_char('\x01')
        else:
            return c_char('\x00')

    def _strToBool(self, s):
        return s != '\x00'
    
    def checkLock(self):
        return self.l.lbnl_check_lock(self.fd) == 0

    def aquireLock(self):
        #library doesn't seem to do anything with param string
        self.fd = self.l.lbnl_open("")
        if self.fd == -4:
            raise LBNLError("Couldn't aquire lock because lock already obtained")
        elif self.fd < 0:
            raise LBNLError("Coundn't aquire lock", self.fd)

    #when you are done; removes lockfile
    def releaseLock(self):
        self.l.lbnl_close(self.fd)

    def init(self):
        error = self.l.lbnl_init(self.fd)
        if error != 0:
            raise LBNLError("init failed", error)

    def ccd_clear(self):
        error = self.l.lbnl_ccd_clear(self.fd)
        if error != 0:
            raise LBNLError("CCD clear failed", error)

    def ccd_erase(self):
        error = self.l.lbnl_ccd_erase(self.fd)
        if error != 0:
            raise LBNLError("CCD erase failed", error)

    def ccd_purge(self):
        error = self.l.lbnl_ccd_purge(self.fd)
        if error != 0:
            raise LBNLError("CCD purge failed", error)

    def ccd_set_purge_params(self, vclk, delay):
        e = self.l.lbnl_ccd_set_purge_params(self.fd, c_float(vclk),
                                             c_int(delay))
        if e != 0:
            raise LBNLError("Setting CCD purge parameters failed", e)

    def ccd_get_purge_params(self):
        vclk = c_float()
        delay = c_int()
        e = self.l.lbnl_ccd_get_purge_params(
             self.fd, byref(vclk), byref(delay))
        if e != 0:
            raise LBNLError("Getting CCD purge parameters failed", e)
        return (vclk.value, delay.value)

    def ccd_read(self):
        r,c = self.ccd_get_size()
        imageData = (c_ushort * (r*c))()
        e = self.l.lbnl_ccd_read(self.fd, imageData)
        if e != 0:
            raise LBNLError("CCD read failed", e)
        return imageData

    def ccd_read_sim(self):
        r,c = self.ccd_get_size()
        imageData = (c_ushort * (r*c))()
        e = self.l.lbnl_ccd_read_sim(self.fd, imageData)
        if e != 0:
            raise LBNLError("simulated CCD read failed", e)
        return imageData

    def readout_prepare(self):
        self.ccd_clear()
        self.ccd_erase()
        self.ccd_purge()
        
    def readout_discard(self):
        error = self.l.lbnl_readout_discard(self.fd)
        if error != 0:
            raise LBNLError("discarding readout failed", error)

    def ccd_set_erase_params(self, vclk, vsub, slew, delay):
        e = self.l.lbnl_ccd_set_erase_params(self.fd,
             c_float(vclk), c_float(vsub), c_int(slew), c_int(delay))
        if e != 0:
            raise LBNLError("Setting CCD erase parameters failed",e)

    def ccd_get_erase_params(self):
        vclk = c_float()
        vsub = c_float()
        slew = c_int()
        delay = c_int()
        e = self.l.lbnl_ccd_get_erase_params(
             self.fd, byref(vclk), byref(vsub), byref(slew), byref(delay))
        if e != 0:
            raise LBNLError("Getting CCD erase parameters failed", e)
        return (vclk.value, vsub.value, slew.value, delay.value)

    def ccd_set_size(self, rows, cols):
        error = self.l.lbnl_ccd_set_size(self.fd,c_ushort(cols), c_ushort(rows))
        if error != 0:
            raise LBNLError("setting CCD size failed", error)

    #returns (rows,cols). note that this is the inverse of the C library
    def ccd_get_size(self):
        rows = c_ushort()
        cols = c_ushort()
        e = self.l.lbnl_ccd_get_size(self.fd, byref(cols), byref(rows))
        if e != 0:
            raise LBNLError("getting CCD size failed", error)
        return (rows.value, cols.value)

    def ccd_idle(self, flag):
        e = self.l.lbnl_ccd_idle(self.fd, self._boolToi8(flag))
        if e != 0:
            raise LBNLError("setting CCD idle state failed", error)

    def readout_get_fits(self, imageData ,filename):
        e = self.l.lbnl_readout_get_fits(self.fd, filename, imageData)
        if e != 0:
            raise LBNLError("failed obtaining fits or writing fits to file", e)

    def readout_get_memfits(self, imageData):
        imptr = c_void_p()
        e = self.l.lbnl_readout_get_memfits(self.fd, imptr, imageData)
        if e != 0:
            raise LBNLError("failed obtaining or writing fits to mem", e)

    def readout_get_status(self):
        status = READOUT()
        e = self.l.lbnl_readout_get_status(self.fd, byref(status))
        if e != 0:
            raise LBNLError("failed getting readout status", error)
        return structToDict(status)

    #returns the controller status as a dict
    def controller_get_status(self):
        s = STATUS()
        error = self.l.lbnl_controller_get_status(self.fd, byref(s))
        if error != 0:
            raise LBNLError("failed getting controller status", error)
        return structToDict(s)

    def controller_upload_timing(self, filepath):
        charptr = c_char_p(filepath)
        e = self.l.lbnl_controller_upload_timing(self.fd, charptr)
        if e != 0:
            raise LBNLError("uploading timing failed", e)

    #start address is the location in the timing file 
    #of the readout routine to use
    def controller_set_start_address(self, start_address):
        sa = c_ushort(start_address)
        e = self.l.lbnl_controller_set_start_address(self.fd, sa)
        if e != 0:
            raise LBNLError("failed setting start address",e)

    def controller_power(self, flag):
        e = self.l.lbnl_controller_power(self.fd, self._boolToi8(flag))
        if e != 0:
            raise LBNLError("setting controller power failed", e)

    #flag = True for master, False for slave
    def controller_master(self, flag):
        flag = self._boolToi8(flag)
        e = self.l.lbnl_controller_master(self.fd, flag)
        if e != 0:
            raise LBNLError("setting controller master failed",e)
    

    #takes 2 lists of bools
    def controller_enable(self, dac_bools, clk_bools):
        if type(dac_bools) == type(clk_bools) == int:
            e = self.l.lbnl_controller_enable(self.fd, dac_bools, clk_bools)
        else:
            dac_mask = c_uint(boolsToMask(dac_bools))
            clk_mask = c_uint(boolsToMask(clk_bools))
            e = self.l.lbnl_controller_enable(self.fd, dac_mask, clk_mask)
        if e != 0:
            raise LBNLError("failed enabling/disbling dacs/clocks",e)

    #takes a list of bools        
    def controller_set_gain(self, bools): 
        if type(bools) == int:
            e = self.l.lbnl_controller_set_gain(self.fd, bools)
        else:
            e = self.l.lbnl_controller_set_gain(self.fd, boolsToMask(bools))
        if e != 0:
            raise LBNLError("setting controller gain failed", e)


    def controller_get_temps(self):
        t1 = c_float()
        t2 = c_float()
        e = self.l.lbnl_controller_get_temps(self.fd,byref(t1),byref(t2))
        if e != 0:
            raise LBNLError("failed getting controller tempuratures", e)
        return (t1.value,t2.value)

    
    #WARNING the methods below are very low level and can screw things up
    def controller_set_dac_value(self, address, value):
        address = c_ushort(address)
        value = c_float(value)
        e = self.l.lbnl_controller_set_dac_value(self.fd, address, value)
        if e != 0:
            raise LBNLError("failed setting DAC value", e)
    
    def controller_set_default_dacs(self):
        e = self.l.lbnl_controller_set_default_dacs(self.fd)
        if e == -1001 or e == -1003:
            print("Couldn't find dac_vals (error %s)" % e)
            print("Proceding with hard-coded defaults")
           
            default_dac_values = (-12, -12, -12, -12, 2.6, 2.6, 2.6, 2.6,
                                   -23, -23, -23, -23, 0, 0, 0, 0, 50)

            for address, value in enumerate(default_dac_values):
                self.controller_set_dac_value(address, value)
        elif e == -1002:
            raise LBNLError("Invalid number in defaults file", e)
        elif e != 0:
            raise LBNLError("Failed setting default DACs vals", e)
        
    def controller_set_default_clks(self):
        e = self.l.lbnl_controller_set_default_clks(self.fd)
        if e == -1001 or e == -1003:
            print("Couldn't find clk_vals (error %s)" % e)
            print("Proceding with hard-coded defaults")

            default_clock_values = ((6,-4),(6,-4),(6,-4),(-6,0),(6,-4),(6,-4),(6,-4),
                                    (-6,0),(5,-3),(5,-3),(5,-3),(5,-3),(5,-3),(5,-3),
                                    (5,-3),(5,-3),(5,-3),(5,-3),(5,-5),(5,-5))
            for address, (high, low) in enumerate(default_clock_values):
	        self.controller_set_clk_value(address, high, low)
        elif e == -1002:
            raise LBNLError("Invalid number in defaults file", e)
        elif e != 0:
            raise LBNLError("Failed setting default clock vals", e)

    def controller_set_clk_value(self, address, high, low):
        address = c_ushort(address)
        high = c_float(high)
        low = c_float(low)
        e= self.l.lbnl_controller_set_clk_value(self.fd, address, high, low)
        if e != 0:
            raise LBNLError("failed setting clock value", e)
        
    def controller_set_delays(self, **deldict):
        delays = DELAYS()
        e = self.l.lbnl_controller_get_delays(self.fd, byref(delays))
        if e != 0:
            raise LBNLError("couldn't get controller delays", e)
        for key, val in deldict.iteritems():
            setattr(delays, key, val)
        e = self.l.lbnl_controller_set_delays(self.fd, delays)
        if e != 0:
            raise LBNLError("failed setting controller delays", e)

    def controller_set_default_delays(self):
        e = self.l.lbnl_controller_set_default_delays(self.fd)
        if e == -1001 or e == -1003:
            print("Couldn't find delay_vals (error %s)" % e)
            print("Proceding with hard-coded defaults")
            self.controller_set_delays()
        elif e == -1002:
            raise LBNLError("Invalid number in defaults file", e)
        elif e != 0:
            raise LBNLError("Failed setting default delay vals", e)

    def controller_get_delays(self):
        delays = DELAYS()
        e = self.l.lbnl_controller_get_delays(self.fd, byref(delays))
        if e != 0:
            raise LBNLError("couldn't get controller delays", e)
        return structToDict(delays)

    def controller_set_cds(self, averaging=9, digioff=0, nsamp_reset=512,
                           nsamp_signal=512):
        cds = CDS(nsamp_signal, nsamp_reset, averaging, digioff)
        e = self.l.lbnl_controller_set_cds(self.fd, cds)
        if e != 0:
            raise LBNLError("failed setting controller cds", e)
    
    def controller_set_default_cds(self):
        e = self.l.lbnl_controller_set_default_cds(self.fd)
        if e == -1001 or e == -1003:
            print("Couldn't find cds_vals (error %s)" % e)
            print("Proceding with hard-coded defaults")
            self.controller_set_cds()
        elif e == -1002:
            raise LBNLError("Invalid number in defaults file", e)
        elif e != 0:
            raise LBNLError("Failed setting default offset vals", e)


    def controller_get_cds(self):
        cds = CDS()
        e = self.l.lbnl_controller_get_cds(self.fd, byref(cds))
        if e != 0:
            raise LBNLError("couldn't get controller cds", e)
        return structToDict(cds)

    def controller_get_ndacs(self):
        ndacs = c_ushort()
        self.l.lbnl_controller_get_ndacs(self.fd, byref(ndacs))
        return ndacs.value

    def controller_get_all_dacs(self):
        ndacs = c_ushort(self.controller_get_ndacs())
        dacs = (DAC * ndacs.value)()
        e = self.l.lbnl_controller_get_all_dacs(self.fd, dacs, byref(ndacs))
        if e != 0:
            raise LBNLError("Failed getting all DACs values", e)
        return [structToDict(dac) for dac in dacs]

    def controller_get_nclocks(self):
        nclocks = c_ushort()
        self.l.lbnl_controller_get_nclocks(self.fd, byref(nclocks))
        return nclocks.value

    def controller_get_all_clocks(self):
        nclocks = c_ushort(self.controller_get_nclocks())
        clocks = (LBNL_CLOCK * nclocks.value)()
        e = self.l.lbnl_controller_get_all_clocks(self.fd, clocks, byref(nclocks))
        if e != 0:
            raise LBNLError("Failed getting all clock values", e)
        return [structToDict(clock) for clock in clocks]
            
    #libCCDController.so doesn't have lbnl_controller_get_all_offsets
    #so cache them at the python level (TODO: correct?)
    _offsets = [None]*8
    def controller_get_all_offsets(self):
        return [{'address':i, 'tvalue': val} for i,val in enumerate(self._offsets)]

    def controller_set_offset_value(self, address, value):
        address = c_ushort(address)
        value = c_float(value)
        e = self.l.lbnl_controller_set_offset_value(self.fd, address, value)
        if e != 0:
            raise LBNLError("failed setting offset value", e)
        self._offsets[address.value] = value.value

    def controller_set_default_offsets(self):
        e = self.l.lbnl_controller_set_default_offsets(self.fd)
        if e == -1001 or e == -1003:
            print("Couldn't find offset_vals (error %s)" % e)
            print("Proceding with hard-coded defaults")

            default_offset_values = (-1.6,)*4 + (0,)*4
            for address, value in enumerate(default_offset_values):
	        self.controller_set_offset_value(address, value)
        elif e == -1002:
            raise LBNLError("Invalid number in defaults file", e)
        elif e != 0:
            raise LBNLError("Failed setting default offset vals", e)

    def controller_get_noffsets(self):
        n = c_ushort()
        e = self.l.lbnl_controller_get_noffsets(self.fd, byref(n))
        if e != 0:
            raise LBNLError("Failed getting number of offsets", e)
        return n.value

    #used in controller_read_register and controller_set_register
    #type_ can be  "videomem", "wavemem", or "gpio"
    #return the value of the symbolic constant correspoinding to _type
    def _register_type(self, type_):
        #symbolic contstants from lbnl_mem.c
        if type_ == "videomem":
            return 2
        elif type_ == "wavemem":
            return 3
        elif type_ == "gpio":
            return 1
        else:
            raise LBNLError("%s is not a valid register type" % type_)


    #type_ can be "videomem", "wavemem", or "gpio"
    def controller_read_register(self, type_, address):
        type_ = self._register_type(type_)
        address = c_ulong(address)
        data = c_ulong()
        e = self.l.lbnl_controller_read_register(self.fd, type_, address, byref(data))
        if e != 0:
            raise LBNLError("Reading register value failed", e)
        return data.value
        

    #type_ can be "videomem", "wavemem", or "gpio"
    def controller_write_register(self, type_, address, regval):
        type_ = self._register_type(type_)
        address = c_ulong(address)
        regval = c_ulong(regval)
        e = self.l.lbnl_controller_write_register(self.fd, type_, address, regval)
        if e != 0:
            raise LBNLError("Wrinting register value failed", e)
