# This file is for quick interactive testing of the CCD controller 
# and it's python wrapper. It is designed to run like 
#    python -i prelude.py


import ccdcontroller
import os

try:
    os.remove('/tmp/lockfile')
except OSError:
    pass

c = ccdcontroller.CCDController()
c.aquireLock()
