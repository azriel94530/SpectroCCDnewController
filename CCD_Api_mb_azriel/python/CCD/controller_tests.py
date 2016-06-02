import unittest
from ccdcontroller import CCDController
from controllercommon import LBNLError

Controller = CCDController

class TestController(unittest.TestCase):
    def setUp(self):
        self.c = Controller()
        self.c.aquireLock()
    
    def tearDown(self):
        self.c.releaseLock()

    def test_ccd_size(self):
        self.c.ccd_set_size(4000,4000)
        self.assertEquals(self.c.ccd_get_size(), (4000,4000))

    def test_sanity_init(self):
        self.c.init()

    def test_sanity_ccd_clear(self):
        self.c.ccd_clear()

    def test_sanity_ccd_erase(self):
        self.c.ccd_erase()

    def test_sanity_ccd_purge(self):
        self.c.ccd_purge()

    def test_sanity_redaout_prepare(self):
        self.c.readout_prepare()

    def test_sanity_readout_discard(self):
        self.c.readout_discard()


if __name__ == "__main__":
    unittest.main()
       
