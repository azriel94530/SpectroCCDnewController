from ctypes import *

class LBNLError(Exception):
    def __init__(self, s, errorno=None):
        self.s = s
        self.errorno = errorno
    def __str__(self):
        if self.errorno == None:
            return self.s
        else:
            return self.s + " (error code: " + str(self.errorno) + ")"

class STATUS(Structure):
    _fields_ = [("power_on", c_char)
               ,("ccd_idle", c_char)
               ,("clk_mask", c_uint)
               ,("dac_mask", c_uint)]

class READOUT(Structure):
    _fields_ = [("progress", c_ushort)  #0 to 100 %
               ,("rows_read", c_ushort) #number of complete rows read
               ]

class DAC(Structure):
    _fields_ = [("address", c_ushort),
                ('tvalue', c_float),
                ('telemetry', c_float),
                ('raw_value', c_ushort),
                ('raw_telemetry', c_ushort)]

class LBNL_CLOCK(Structure):
    _fields_ = [("address", c_ushort),
                ("tlow_value", c_float),
                ("thigh_value", c_float),
                ('telemetry', c_float),
                ('raw_telemetry', c_ushort),
                ('low_raw_value', c_ushort),
                ('high_raw_value', c_ushort)]


FAILED = -10
WRONG_HANDLE = -3
LOCKED = -4

def boolsToMask(bs):
    return int(''.join(['1' if b else '0' for b in bs]),2)

def maskToBools(m):
    return [c == '1' for c in'{0:b}'.format(m)]

def structToDict(struct):
    d = {}
    for field, _ in struct._fields_:
        d[field] = getattr(struct, field)
    return d
