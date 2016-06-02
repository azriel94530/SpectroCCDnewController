#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <stdarg.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <fcntl.h>
#include <string.h>
#include <strings.h>
#include <sys/time.h>
#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <sys/un.h>
#include <pthread.h>
#include <syslog.h>
#include "../lbnl_typedefs.h"

#define BPP	2
#define MAXCMDWORDS	12
#define MAXRESPWORDS	12

//#include "tcplinux.h"
#define LBNL_SOCKET_STR	"/tmp/lbnld.sock"
#define LBNL_MAX_CONNECT	2
#define	LBNL_SHUTDOWN	99
#define	LBNL_OPEN	1
#define	LBNL_READ	2
#define	LBNL_WRITE	3
#define	LBNL_CLOSE	4
#define LBNL_IMAGE	5
#define	LBNL_IMSIZE	6
#define	LBNL_PROGRESS	7
#define	LBNL_CCD_CLEAR	8
#define	LBNL_CCD_ERASE	9
#define	LBNL_CCD_PURGE	10
#define	LBNL_GET_IMSIZE	11
#define	LBNL_IDLE	12
#define	LBNL_POWER	13
#define	LBNL_ENABLE	14
#define	LBNL_GAIN	15
#define	LBNL_TEMPS	16
#define	LBNL_GET_DACS	17
#define	LBNL_GET_NDACS	18
#define	LBNL_GET_CLKS	19
#define	LBNL_GET_NCLKS	20
#define	LBNL_LOAD_TIM	21
#define	LBNL_DEFAUL_TIM	22
#define	LBNL_SET_CDS	23
#define	LBNL_GET_CDS	24
#define	LBNL_SET_DAC	25
#define	LBNL_FITS	26
#define LBNL_GET_PROG	27
#define LBNL_GET_STAT	28
#define LBNL_SET_DELAY	29
#define LBNL_SET_CLK	30
#define LBNL_SET_OFF	31
#define LBNL_SET_EXPT	32
#define LBNL_EXP_ADD    33
#define	LBNL_GET_OFF	34
#define	LBNL_GET_NOFF	35
#define LBNL_GET_DELAYS	36
#define LBNL_GET_REG	37
#define LBNL_SET_REG	38
#define LBNL_ARTIF_DATA	39
#define LBNL_SET_CPARS	40
#define LBNL_SET_EPARS	41
#define LBNL_SET_PPARS	42
#define LBNL_GET_CPARS	43
#define LBNL_GET_EPARS	44
#define LBNL_GET_PPARS	45

#ifdef _DEBUG_
#  define pdebug(fmt, args...) printf ("lbnldaemon: " fmt, ## args)
#else
#  define pdebug(fmt, args...)
#endif

typedef unsigned int lbnldata_t;
typedef unsigned int lbnladd_t;

typedef struct {
	int cmd;
	int nw;
	char strmsg[128];
	lbnldata_t data[MAXCMDWORDS];
} cmdstruct_t;

typedef struct {
        char strmsg[128];
        lbnldata_t data[MAXRESPWORDS];
        int status;
} respstruct_t;

typedef struct {
        int status;
        dac_t *dacs;
} dacresp_t;
