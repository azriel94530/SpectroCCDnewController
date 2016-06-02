import unittest
from ccdcontroller import CCDController
from faux_ccdcontroller import SimulatedCCDController
from controllercommon import *

Controller = SimulatedCCDController

class TestFakeCCDControllerLocking(unittest.TestCase):
    def test_lock(self):
        c = Controller()
        self.assertFalse(c.checkLock())
        c.aquireLock()
        self.assertTrue(c.checkLock())
        c.releaseLock()
        self.assertFalse(c.checkLock())

    def test_double_close(self):
        c = Controller()
        self.assertRaises(LBNLError, c.releaseLock)

    def test_double_open(self):
        c = Controller()
        c.aquireLock()
        self.assertRaises(LBNLError, c.aquireLock)


    def test_requires_lock(self):
        methods = ["init", 'ccd_clear','ccd_purge', 'ccd_erase', 'readout_prepare', 'readout_discard', 'ccd_get_size', 'readout_get_status', 'controller_get_temps', 'controller_get_status']
        for m in methods:
            c = Controller()
            #print m
            self.assertRaises(LBNLError, getattr(c, m))

class TestController(unittest.TestCase):
    def setUp(self):
        self.c = Controller()
        self.c.aquireLock()
    
    def tearDown(self):
        self.c.releaseLock()

    def test_ccd_size(self):
        self.assertEquals(self.c.ccd_get_size(),(4200,4200))
        self.c.ccd_set_size(4000,4000)
        self.assertEquals(self.c.ccd_get_size(), (4000,4000))

class TestCommon(unittest.TestCase):
    def test_boolsToMask(self):
        self.assertEquals(boolsToMask([False,False,False,True,False, True]), 5)
        self.assertEquals(boolsToMask([False]),0)
        self.assertEquals(boolsToMask([True]),1)
    
    def test_maskToBools(self):
        self.assertEquals(maskToBools(37),[True,False,False,True,False,True])
        self.assertEquals(maskToBools(0),[False])

    def test_inverse(self):
        for i in xrange(100):
            self.assertEquals(boolsToMask(maskToBools(i)),i)

if __name__ == "__main__":
    unittest.main()
       
