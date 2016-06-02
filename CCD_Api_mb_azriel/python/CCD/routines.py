import time

#given an application framework app, log to it at the info level
#if the app doesn't exist, don't complain, instead print to stdout
def info(app, message):
    if app == None:
        print(message)
    else:
        app.info(message)

def digitize(c, exposure_time, app=None):
    info(app, "Exposure triggered")

    header_info = {}
    header_info["exposure_time"] = exposure_time

    #TODO should this be here at all?
    c.controller_power(True) #where?
    c.init() #where?    

    info(app, 'exposure started')
    c.ccd_idle(False)
    time.sleep(exposure_time)
    info(app, 'exposure finished')
    info(app, 'readout started')
    t1 = time.time()
    image_data = c.ccd_read()
    t2 = time.time()
    print('readout finished (time: %s)' % (t2 - t1))

    return (image_data, header_info)

def set_default_values(c, start_address, app=None):
    info(app, 'setting default DACs values')
    c.controller_set_default_dacs()
    
    info(app, 'setting default clock values')
    c.controller_set_default_clks()

    info(app, 'setting default offsets')
    c.controller_set_default_offsets()

    info(app, 'setting default CDS values')
    c.controller_set_default_cds()

    info(app, 'setting default delays')
    c.controller_set_default_delays()

    # [T,F,T] ~ 101 ~ 5
    info(app, 'setting gains')
    c.controller_set_gain([True, False, True])

    #size would be set here

    info(app, 'enabling DACs and clocks')
    #constants taken from lbnl_typedefs.h
    DACMASK = 0x7f3f3f3f
    CLKMASK = 0xfffff
    c.controller_enable(DACMASK, CLKMASK)

    #where?
    start_address = start_address
    info(app, 'setting start address to %d' % start_address)
    c.controller_set_start_address(start_address)

def reset(c, app=None):
    c.controller_master(True)
    c.controller_power(True)
    time.sleep(.1)
    c.init()
    c.ccd_idle(True)
    
