#! /usr/bin/env python

import cmd
import routines
import os
import argparse

class CCDShell(cmd.Cmd):
    """Shell for interactively taking CCD exposures"""
    
    intro = "CCD exposure shell: type help to see a list of commands"

    _default_start_address = 32 #TODO should this be changeable?
    _fits_location = "/home/freddy/test.fits"


    def __init__(self,simulate=False):
        cmd.Cmd.__init__(self)
        self.simulate = simulate

    #setup
    def preloop(self):
        if self.simulate:
            import faux_ccdcontroller
            self.c = faux_ccdcontroller.SimulatedCCDController()
        else:
            import ccdcontroller
            self.c = ccdcontroller.CCDController()
        self.c.aquireLock()
        routines.set_default_values(self.c, self._default_start_address)
        self.do_set_timing(
            "/home/freddy/ccdcontroller/config/timing.txt")

    #tear-down
    def postloop(self):
        self.c.releaseLock()

    #exit cleanly when user pressed ctrl-d
    def do_EOF(self, line):
        """press ctrl-d to exit the program"""
        print('')
        return True

    def do_exit(self, line):
        """Exit the CCD shell"""
        return True

    #don't repeat the last command on a empty line
    def emptyline(self):
        pass

    def do_get_temps(self, line):
        """get_temps\n Print the tempuratures"""
        if line != "":
            print("get_temps takes no arguments")
            return
        temps = self.c.controller_get_temps()
        print("Tempuratures: %s, %s" % temps)

    def do_get_dacs(self, line):
        """get_dacs\n Print all DACs values"""
        if line != "":
             print("error: get_dacs takes no arguments")
             return
        dacs = self.c.controller_get_all_dacs()
        for dac in dacs:
            print(', '.join(['%s: %s' % (k,v) for k,v in sorted(dac.iteritems())]))

    def do_get_clocks(self, line):
        """get_clocks\n print all clock values"""
        if line != '':
            print("error: get_clks takes no arguments")
            return
        clks = self.c.controller_get_all_clocks()
        for clk in clks:
            print(', '.join(['%s: %s' % (k,v) for k,v in sorted(clk.iteritems())]))

    def do_get_offsets(self, line):
        """get_offsets\n print all offset values"""
        if line != "":
            print("error: get_offsets takes no arguments")
            return
        offsets = self.c.controller_get_all_offsets()
        for offset in offsets:
            print("address: %s, tvalue: %s" % 
                  (offset['address'], offset['tvalue']))

    def do_get_delays(self, line):
        """get_delays\n print all delay values"""
        if line != "":
            print("error: get_delays takes no arguments")
            return
        delays = self.c.controller_get_delays()
        for k, v in delays.iteritems():
            print("%s: %s" % (k,v))

    def do_get_cds(self, line):
        """get_cds\n print all cds params"""
        if line != "":
            print("error: get_cds takes no arguments")
            return
        cds = self.c.controller_get_cds()
        for k,v in cds.iteritems():
            print("%s: %s" % (k,v))            

    def do_get_size(self, line):
        """get_size\n get image resolution"""
        if line != "":
            print("error: get_size takes no arguments")
            return
        size = self.c.ccd_get_size()
        print("cols: %s\nrows: %s" % size[::-1])

    def do_set_size(self, line):
        """set_size cols rows\n set image resolution"""
        try:
            line = line.split(' ')
            cols = int(line[0])
            rows = int(line[1])
        except Exception as e:
            print("error: set_size take two integer arguments")
            print(e)
            return
        self.c.ccd_set_size(rows, cols)

    def do_take_exposure(self, t):
        """take_exposure [t]\n Take an exposure of time t seconds (defaults to 1 if not supplied)"""
        if t == '':
            t = 1
        else:
            try:
                t = int(t)
            except ValueError:
                print("error: invalid time")
                return
        
        data = routines.digitize(self.c, t)
        self.c.readout_get_fits(data, self._fits_location)

    def do_reset_controller(self, line):
        """reset_controller\n Reset the controller. (set master, power on, initialize, idle)"""
        if line != "":
            print("reset_controller takes no arguments")
            return
        routines.reset(self.c)
        
    def do_set_fits(self, filepath):
        """set_output filepath\n Set the output location for the FITS image (default = test.fits)"""
        if filepath == '':
            print "take_exposure requires a FITS file location as its argument"
            return
        try:
            open((filepath), 'w').close()
        except (OSError, IOError) as e:
            print('please provide a valid filename')
            print(e)
            return
        self._fits_location = filepath

    def do_get_fits(self, line):
        """get_fits\n Print FITS file output location"""
        if line != '':
            print("error: get_fits takes no arguments")
            return
        print("FITS output location: %s" % self._fits_location)

    def do_set_timing(self, filepath):
        """set_timing filepath\n Set the location of the timing file (default = /home/freddy/ccdcontroller/config/timing.txt)"""
        if filepath == '':
            print "take_exposure requires a timing file as its argument"
            return
        try:
            open((filepath), 'r').close()
        except (OSError, IOError) as e:
            print('please provide a valid file')
            print(e)
            return
        print("Setting timing file location to " + filepath)
        self.c.controller_upload_timing(filepath)
        self._timing_location = filepath

    def do_get_timing(self, line):
        """get_timing\n Print timing file location"""
        if line != '':
            print("error: get_timing takes no arguments")
            return
        try:
            print("Timing file location: %s" % self._timing_location)
        except AttributeError as e:
            print("error: timing file location not set")
    
    def do_erase(self, line):
        """erase\n Erase the CCD"""
        if line != '':
            print("error: erase takes no arguments")
            return
        self.c.ccd_erase()
        print('CCD erased')

    def do_purge(self, line):
        """purge\n Purge the CCD"""
        if line != '':
            print("error: purge takes no arguments")
            return
        self.c.ccd_purge
        print('CCD purged')

    def do_clear(self, line):
        """clear\n Clear the CCD"""
        if line != '':
            print("error: clear takes no arguments")
            return
        self.c.ccd_clear()
        print('CCD cleared')

    def do_prepare(self, line):
        """prepare\n Clear, erase, and purge the CCD"""
        if line != '':
            print("error: prepare takes no arguments")
            return
        self.c.ccd_clear()
        print('CCD cleared')
        self.c.ccd_erase()
        print('CCD erased')
        self.c.ccd_purge()
        print('CCD purged')

    def do_set_erase_params(self, line):
        """set_erase_params vclk vsub slew delay\n set parameters for CCD purge"""
        try:
            line = line.split(' ')
            vclk = float(line[0])
            vsub = float(line[1])
            slew = int(line[2])
            delay = int(line[3])
        except Exception as e:
            print("error: set_erase_params takes four arguments")
            print(e)
            return
        self.c.ccd_set_erase_params(vclk, vsub, slew, delay)

    def do_get_erase_params(self, line):
        """get_erase_params\n print the parameters to CCD erase"""
        if line != '':
            print("error: get_erase_params takes no arguments")
            return
        params = self.c.ccd_get_erase_params()
        print("vclk: %s\nvsub: %s\nslew: %s\ndelay: %s" % params)

    def do_set_purge_params(self, line):
        """set_purge_params vclk delay\n set the parameters to CCD purge"""
        try:
            line = line.split(' ')
            vclk = float(line[0])
            delay = int(line[1])
        except Exception as e:
            print("error: set_purge_params takes two arguments")
            print(e)
            return
        self.c.ccd_set_purge_params(vclk, delay)

    def do_get_purge_params(self, line):
        """get_purge_params\n print the parameters to CCD purge"""
        if line != '':
            print("error: get_purge_params takes no arguments")
            return
        params = self.c.ccd_get_purge_params()
        print("vclk: %s\ndelay: %s" % params)

    #engineering level commands

    def do_set_dac(self, line):
        """WARNING: ENGINEERING LEVEL COMMAND\nsyntax: set_dac address [val]"""
        try:
            line = line.split(' ')
            address = int(line[0])
            if len(line) == 1:
                value = routines.default_dac_values[address]
            else:
                value = float(line[1])
        except Exception as e:
            print("set_dac takes an address and a floating point value as arguments")
            print(e)
            return
        self.c.controller_set_dac_value(address, value)

    def do_reset_dacs(self, line):
        """dacs\n set all dacs to default values"""
        if line != '':
            print("error: reset_dacs takes no arguments")
            return
        self.c.controller_set_default_dacs()

    def do_set_clock(self, line):
        """WARNING: ENGINEERING LEVEL COMMAND\nsyntax: set_clock address [high low]"""
        try:
            line = line.split(' ')
            address = int(line[0])
            if len(line) == 1:
                high,low = routines.default_clock_values[address]
            else:
                high = float(line[1])
                low = float(line[2])
        except Exception as e:
            print("set_clock takes an address and two floating point value as arguments")
            print(e)
            return
        self.c.controller_set_clk_value(address, high, low)
 
    def do_reset_clocks(self, line):
        """reset_clocks\n set all clocks to default values"""
        if line != '':
            print("error: reset_clocks takes no arguments")
            return
        self.c.controller_set_default_clks()
    

    def do_set_offset(self, line):
        """WARNING: ENGINEERING LEVEL COMMAND\n\nsyntax: set_offset address [val]"""
        try:
            line = line.split(' ')
            address = int(line[0])
            if len(line) == 1:
                value = routines.default_offset_values[address]
            else:
                value = float(line[1])
        except Exception as e:
            print("set_offset take an address and a floating point value as arguments")
            print(e)
            return
        self.c.controller_set_offset_value(address, value)

    def do_reset_offsets(self, line):
        """reset_offsetss\n set all offsets to default values"""
        if line != '':
            print("error: reset_offsets takes no arguments")
            return
        self.c.controller_set_default_offsets()

    def do_set_delay(self, line):
        """WARNING: ENGINEERING LEVEL COMMAND\n\nsyntax: set_delay name val"""
        try:
            line = line.split(' ')
            param = line[0]
            val = int(line[1])
        except Exception as e:
            print("set_delay takes one string and one int as arguments")
            print(e)
            return
        if param not in ["settling_signal","settling_reset", 
                         "clock_serial", "clock_sumwell", "clock_reset",
                         "clock_parallel", "other1", "other2", "other3",
                         "other4"]:
            print("Invalid parameter: %s" % param)
            return
        self.c.controller_set_delays(**{param: val})

    def do_reset_delays(self, line):
        """syntax: reset_delay"""
        if line != "":
            print("error: reset_delays takes no arguments")
            return
        self.c.controller_set_default_delays()

    def do_set_cds(self, line):
        """WARNING: ENGINEERING LEVEL COMMAND\n\nsyntax: set_cds name val"""
        try:
            line = line.split(' ')
            param = line[0]
            val = int(line[1])
        except Exception as e:
            print("set_cds takes one string and one int as arguments")
            print(e)
            return
        if param not in ["nsamp_signal", "nsamp_reset", "averaging", 
                         "digioff"]:
            print("Invalid parameter: %s" % param)
            return
        self.c.controller_set_cds(**{param: val})

    def do_reset_cds(self, line):
        """syntax: reset_cds"""
        if line != "":
            print("error: reset_cds takes no arguments")
            return
        self.c.controller_set_default_cds()

    def do_write_register(self, line):
        '''WARNING: ENGINEERING LEVEL COMMAND\nwrite_register type address\n type can be "videomem", "wavemem", or "gpio"'''
        if self.simulate:
            print("Not supported with simluated CCD")
            return 
        try:
            line = line.split(' ')
            type_ = line[0]
            address = int(line[1])
            regval = int(line[2])
        except Exception as e:
            print('error: read_register takes on string and one interger as arguments')
            print(e)
            return
        if type_ not in ["videomem", "wavemem", "gpio"]:
            print("error: Invalid register type")
            return
        self.c.controller_write_register(type_, address, regval)


    def do_read_register(self, line):
        '''WARNING: ENGINEERING LEVEL COMMAND\nread_register type address\n type can be "videomem", "wavemem", or "gpio"'''
        if self.simulate:
            print("Not supported with simluated CCD")
            return 
        try:
            line = line.split(' ')
            type_ = line[0]
            address = int(line[1])
        except Exception as e:
            print('error: read_register takes on string and one interger as arguments')
            print(e)
            return
        if type_ not in ["videomem", "wavemem", "gpio"]:
            print("error: Invalid register type")
            return
        print(self.c.controller_read_register(type_, address))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="main.py", description="CCD shell")
    parser.add_argument("-s", dest='simulate', action='store_true')
    parser.set_defaults(simulate=False)
    args = parser.parse_args()

    #separate the imports to avoid unneeded dependancies
    if not args.simulate:
        #delete the lockfile if it exits
        try:
            os.remove('/tmp/lockfile')
        except OSError:
            pass
    else:
        import faux_ccdcontroller

    CCDShell(args.simulate).cmdloop()
