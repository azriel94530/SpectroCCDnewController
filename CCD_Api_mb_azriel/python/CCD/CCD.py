#!/usr/bin/env python

from DOSlib.application import Application
import DOSlib.discovery as discovery
import ccdcontroller
import faux_ccdcontroller
import time
import threading
import routines

class CCD(Application):
    tag = 'ICS' #TODO is this right?
    commands = ['configure', 'digitize', 'get_fragment', 'checkLock', 'reset', 'set_size',
                'get_size', 'readout_prepare', 'ccd_clear', 'ccd_erase',
                'ccd_purge', 'ccd_idle', 'readout_get_status', 
                'controller_get_status', 'controller_upload_timing',
                'controller_set_start_address', 'controller_power']

    #note: 'rows' and 'columns' are only the initial settings, and
    #and may change without being reflected in self.config 
    defaults = {'simulate': True, 'rows': 4200, 'columns':4200, 
                'timing_file': 
                "/home/freddy/ccdcontroller/config/timing.txt",
                'exposure_time': 1, 'start_address': 32, "maxbuffers":4}

    _buffers = {}
    _lock = threading.Lock()

    def lock(f):
        """decorator: aquire lock before running and release when done.
        immediately return error message if lock is closed"""
        def wrapper(*args, **kwargs):
            self = args[0]
            if not self._lock.acquire(False):
                return 'FAILED: CCD is busy'
            r = f(*args, **kwargs)
            self._lock.release()
            return r
        return wrapper
            
    def init(self):
        """Initialize CCD appliation.  Start Library wrapper, obtain lock"""
        self.info('INITIALIZING Role %s' % self.role)
        self.loglevel('INFO')
        
        self.config['rows'] = int(self.config['rows'])
        self.config['columns'] = int(self.config['columns'])

        #self.c is the CCD controller
        if self.config['simulate']:
            self.c = faux_ccdcontroller.SimulatedCCDController()
            self._fits_write_location = 'test.fits'
        else:
            self.c = ccdcontroller.CCDController()
            self._fits_write_location = '/dev/shm/test.fit'
            
        self.info("aquiring lock")
        self.c.aquireLock()
        self.debug("lock aquired")
        
        self.info("setting size with config values")
        self.c.ccd_set_size(self.config['rows'], self.config['columns'])
        self.debug("size set")
    
        self.info("Setting default values")
        routines.set_default_values(self.c, self.config['start_address'], self)
        self.debug("default values set")
        
    def configure(self, constants):
        self.info('configuring: empty procedure')
        
        # this is where the defaults set with routines.set_default_values
        # in init are to be overriden with values from the database

        #what does this do?
        return self.SUCCESS

    def main(self):
        self.info('CCD is operational')
        while not self.shutdown_event.isSet():
            time.sleep(10)
        
        if self.c.checkLock():
            self.info("Powering down controller")
            self.c.controller_power(False) #TODO ???
            self.info("releasing lock")
            self.c.releaseLock()
    
    def checkLock(self, args):
        return self.c.checkLock()

    #Todo aquire lock, release lock?  I don't think so.

    @lock
    def controller_init(self, args):
        self.c.init()

    @lock
    def readout_prepare(self, args):
        self.info('Clearing CCD')
        self.c.ccd_clear()
        self.info('Erasing CCD')
        self.c.ccd_erase()
        self.info('Purging CCD')
        self.c.ccd_purge()
            
    @lock
    def ccd_clear(self):
        self.info('Clearing CCD')
        self.c.ccd_clear()

    @lock
    def ccd_erase(self):
        self.info('Erasing CCD')
        self.c.ccd_erase()

    @lock
    def ccd_purge(self):
        self.info('Purging CCD')
        self.c.ccd_purge()

    @lock
    def ccd_idle(self, args):
        if args == "":
            return 'Failed: expects exactly 1 boolean argument'
        
        if type(args) == bool:
            flag = args
        elif 'F' in args:
            flag = False
        else:
            flag = True
        self.c.ccd_idle(flag)

    def readout_get_status(self, args):
        if args != '':
            return "FAILED: readout_get_status doesn't take any args"
        return self.c.readout_get_status()

    def controller_get_status(self, args):
        if args != '':
            return "FAILED: controller_get_status doesn't take any args"
        return self.c.controller_get_status()

    @lock
    def controller_upload_timing(self, args):
        if ' ' in args:
            return "Failed: controller_upload_timing takes a filepath as it's argument"
        self.config['timing_file'] = args
        self.c.controller_upload_timing(args)
    
    @lock
    def controller_set_start_address(self, args):
        address = int(args)
        self.config['start_address'] = address
        self.c.controller_set_start_address(address)
        
    @lock
    def controller_power(self, args):
        if args == '':
            return 'Failed: expects single boolean arg'

        if type(args) == bool:
            flag = args
        elif 'F' in args:
            flag = False
        else:
            flag = True
        self.c.controller_power(flag)

    @lock
    def reset(self, args):
        self.info("Resetting")
        self.c.controller_power(True)
        self.c.ccd_idle(True)
        self.info("Reset finished")

    def get_size(self, args):
        return self.c.ccd_get_size()
    
    @lock
    def set_size(self, args):
        args = args.split(' ')
        if len(args) != 2:
            return "FAILED: expected exactly two arguments"
        r = int(args[0])
        c = int(args[1])
        
        self.c.ccd_set_size(r,c)

    @lock
    def digitize(self, ID, exposure_time):
        """digitize CCD, if there is an internal buffer available"""
        if len(self._buffers) == self.config['maxbuffers']:
            return "FAILED: all buffers full"
        if ID in self._buffers:
            return "FAILED: already have image for " + str(ID)

        self.info('digitize triggered')

        self.info('getting temps')
        header_info = {}
        t1, t2 = c.controller_get_temps()
        info(app, "Temperature: %d, %d" % (t1, t2))
        header_info["t1"] = t1
        header_info["t2"] = t2

        self.info("digitizing")
        data = routines.digitize(self.c, exposure_time, self)
        self._buffers[ID] = data, header_info

    def get_fragment(self, ID, release=True):
        if ID not in self._buffers:
            return "FAILED: no buffer for " + str(ID)
        self.info("sending fragment out")
        image_data, header_info = self._buffers[ID]
        if release:
            del(self._buffers[ID])
        return (ID, bytearray(image_data), header_info)
    
        
        
if __name__ == '__main__':
    CCD().run()
