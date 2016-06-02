CC= gcc
CFLAGS = -Wall -g -O -fPIC
INCLUDES = -I /usr/src/linuc/include -I.

SRCS = lbnlLib.c lbnl_mem.c lbnl_spi.c RTDmath.c
OBJS = $(SRCS:.c=.o)
SLIBS = ../lib
LIBS = -lm

MAIN = main 

OSBIT = $(shell getconf LONG_BIT)
ifeq ($(OSBIT), 64)
        OS = -DOS64
        FFLAG = -fpic
else
        OS = -DOS32
        FFLAG =
endif

all: clean $(MAIN)

$(MAIN): sharedlib $(SLIBS)/libCCDcontroller.so
	$(CC) $(CFLAGS) $(OS) $(FFLAG) $(INCLUDES) $(LIBS) -L$(SLIBS) -l CCDcontroller main.c -o $(MAIN)

apilib: $(OBJS)
	ar cr $(SLIBS)/libAPI.a $(OBJS)

sharedlib: $(OBJS) $(SLIBS)/libcfitsio.a apilib
	gcc -shared -fPIC -o $(SLIBS)/libCCDcontroller.so -Wl,--whole-archive $(SLIBS)/libcfitsio.a $(SLIBS)/libAPI.a -Wl,--no-whole-archive

.c.o:
	$(CC) $(CFLAGS) $(OS) $(FFLAG) $(INCLUDES) -c $< -o $@

clean: 
	-rm -f *.so* *.o *.out

depend: $(SRCS)
	makedepend $(INCLUDES) $^

# DO NOT DELETE THIS LINE -- make depend needs it

