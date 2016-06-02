#include "lbnld.h"
#include "daemon_defs.h"
#include "../lbnl_prototypes.h"
#include <errno.h>
//#include <lbnl_typedefs.h>

int got_sigterm=0;
int listenfd;
dref dfd;
unsigned int bsize;
u16 *imbuffer;

int main(int argc, char **argv)
  {
  int              connfd, len;
  socklen_t        clilen, addrlen;
  struct sockaddr_in address,remote;
  pthread_t        tid;

  if ((listenfd = socket(AF_INET,SOCK_STREAM,0)) > 0)
	printf ("socket was created\n");
  address.sin_family = AF_INET;
  address.sin_addr.s_addr = INADDR_ANY;
  address.sin_port = htons(15001);
  if (bind(listenfd,(struct sockaddr *) &address, sizeof(address)) == 0)
        printf("Binding Socket\n");

  listen (listenfd,LBNL_MAX_CONNECT);
  signal(SIGINT, signal_handler);
  signal(SIGPIPE, signal_handler);
  signal(SIGHUP,signal_handler); /* catch hangup signal */
  signal(SIGTERM,signal_handler); /* catch kill signal */
  addrlen = sizeof(struct sockaddr_in);
  while (!got_sigterm) {
    clilen = addrlen;
    printf ("accepting conenctions\n");
    len = sizeof(remote);
    connfd = accept(listenfd, (struct sockaddr *)&remote, (socklen_t *)&len);
    if (connfd > 0){
	printf ("connected %d\n", connfd);
	pthread_create(&tid, NULL, &thread_main, (void *)connfd);
    } else
	printf ("got wrong connection (%d %d)\n", connfd, errno);
  }
  pthread_join(tid,NULL);
  return(0);
  }

int allocate_buffer (int nbytes)
{
	if (bsize >= nbytes)
		return (0);
	if (imbuffer != NULL) {
		free (imbuffer);
		bsize = 0;
		imbuffer = NULL;
	}
//	imbuffer = (unsigned short *) malloc (nbytes);
	imbuffer = (i16 *) malloc (nbytes);
//	*imbuffer = 121;
	if (imbuffer == NULL)
		return (-ENOMEM);
	bsize = nbytes;
	return (0);
}

/*-----------------------------------------------------------------------------
| thread_main -- main function for threads:
|
-----------------------------------------------------------------------------*/
void *thread_main(void *arg)
  {
  int  cin, fdin;
  cmdstruct_t message;
  respstruct_t response;
  fdin=(int)arg;
  int ret;
  lbnldata_t val, raddr;
//  dref dfd;
  int bsize=0;
  int nbytes;
  unsigned short aux1, aux2;
  unsigned short artif_data=0;
  data_t regval;
  f32 faux1, faux2;
  dac_t *dacs;
  cds_t cds;
  readout_t readstat;
  delays_t delay;
  status_t constat;
  lbnl_clock_t *clocks;
  unsigned short ndacs;
  i32 iaux1, iaux2;
//  dacresp_t dacresp;

  do {
    if ((cin=recv(fdin,&message,sizeof(cmdstruct_t), 0))!=sizeof(cmdstruct_t)){
	pdebug ("bad message, connection closed\n");
	printf("received socket data wrong size %d", cin);
	close (fdin);
	cin = 0;
    } else {
    	printf ("cmd %d\n", message.cmd);
	switch (message.cmd) {
		case LBNL_OPEN:
			ret = 0;
			if (dfd == 0){
			  	if ((dfd=lbnl_open (NULL))<0){
					 printf ("error opening %d\n", dfd);
	 	         		 sprintf (response.strmsg, "ERROR opening %d\n",dfd);
	    	      			 lbnl_close (dfd);
	    	      			 ret = dfd;
			 	} else {
			 		sprintf (response.strmsg, "DONE");
				}
			} else {
	 	         	sprintf (response.strmsg, "Already opened");
			}
			 response.status = ret;
			 send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
		case LBNL_CLOSE:
			lbnl_close (dfd);
			printf ("cmd: CLOSE\n");
			response.status = 0;
			sprintf (response.strmsg, "DONE");
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			sleep (1);
			close (fdin);
			fdin = 0;
			cin = 0;

			// Azriel try and reset the driver handle so that new opens can happen
			dfd = 0;
			// end of added block

			break;
        case LBNL_IMSIZE:
            printf ("cmd: IMSIZE\ndata: %d %d\n", message.data[0], message.data[1]);
			if ((ret=lbnl_ccd_set_size (dfd, message.data[0], message.data[1]))!=0){
                 printf ("ERROR %d\n",ret);
                 sprintf (response.strmsg, "ERROR %d\n",ret);
            } else {
				nbytes = message.data[0] * message.data[1] * BPP;
				if (nbytes > 0){
					printf ("allocating buffer for %d bytes\n", nbytes);
					if ((ret=allocate_buffer (nbytes)) <0)
                             sprintf (response.strmsg, "ERROR allocating buffer %d\n", ret);
					else
                             sprintf (response.strmsg, "DONE");
				} else {
					ret = -22;
                    sprintf (response.strmsg, "ERROR trying to allocat 0 bytes buffer\n");
				}
            }
			printf ("buffer %s\n", response.strmsg);
		       response.status = ret;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
        case LBNL_ARTIF_DATA:
            printf ("cmd: ARTIF_DATA %d\n", message.data[0]);
            artif_data = message.data[0];
 		    response.status = 0;
 		    sprintf (response.strmsg, "DONE");
 			send (fdin, (void *)&response, sizeof (respstruct_t),0);
 			break;
        case LBNL_GET_IMSIZE:
            printf ("cmd: GET_IMSIZE\n");
			if ((ret=lbnl_ccd_get_size (dfd, &aux1, &aux2))!=0){
                      printf ("ERROR %d\n",ret);
                      sprintf (response.strmsg, "ERROR %d\n",ret);
            } else {
                      sprintf (response.strmsg, "DONE");
			}
		    response.status = ret;
		    response.data[0] = (u32) aux1;
		    response.data[1] = (u32) aux2;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
         case LBNL_GET_REG:
            printf ("cmd: GET_REG %d %d\n", message.data[0], message.data[1]);
			if ((ret=lbnl_controller_read_register (dfd, message.data[0], message.data[1], &regval))!=0){
                       printf ("ERROR %d\n",ret);
                       sprintf (response.strmsg, "ERROR %d\n",ret);
             } else {
                       sprintf (response.strmsg, "DONE");
			}
		    response.status = ret;
		    response.data[0] = (u32) regval;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
         case LBNL_SET_CDS:
            printf ("cmd: CDS\ndata:\n");
		 	cds.nsamp_signal = message.data[0];	
		 	cds.nsamp_reset = message.data[1];	
		 	cds.averaging = message.data[2];	
		 	cds.digioff = message.data[3];	
			printf ("nsamp_signal %d, nsamp_reset %d, averaging %d, digioff %d\n", cds.nsamp_signal, cds.nsamp_reset, cds.averaging, cds.digioff);
			if ((ret=lbnl_controller_set_cds (dfd, cds))!=0){
                        printf ("ERROR %d\n",ret);
                        sprintf (response.strmsg, "ERROR %d\n",ret);
             } else {
				        printf ("CDS OK\n");
                        sprintf (response.strmsg, "DONE");
			}
		    response.status = ret;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
         case LBNL_SET_DELAY:
            printf ("cmd: DELAYS\ndata:\n");
		 	delay.settling_signal = message.data[0];	
		 	delay.settling_reset = message.data[1];	
		 	delay.clock_serial = message.data[2];	
		 	delay.clock_sumwell = message.data[3];	
		 	delay.clock_reset = message.data[4];	
		 	delay.clock_parallel = message.data[5];	
		 	delay.other1 = message.data[6];	
		 	delay.other2 = message.data[7];	
		 	delay.other3 = message.data[8];	
		 	delay.other4 = message.data[9];	
			if ((ret=lbnl_controller_set_delays (dfd, delay))<0){
                     printf ("ERROR %d\n",ret);
                     sprintf (response.strmsg, "ERROR %d\n",ret);
             } else {
				      printf ("DELAYS OK\n");
                      sprintf (response.strmsg, "DONE");
			}
		    response.status = ret;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
         case LBNL_GET_CDS:
            printf ("cmd: GET_CDS\n");
			if ((ret=lbnl_controller_get_cds (dfd, &cds))!=0){
                      printf ("ERROR %d\n",ret);
                      sprintf (response.strmsg, "ERROR %d\n",ret);
            } else {
                      sprintf (response.strmsg, "DONE");
			}
		    response.status = ret;
		    response.data[0] = cds.nsamp_signal;
		    response.data[1] = cds.nsamp_reset;
		    response.data[2] = cds.averaging;
		    response.data[3] = cds.digioff;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
         case LBNL_GET_DELAYS:
            printf ("cmd: GET_DELAYS\n");
     		if ((ret=lbnl_controller_get_delays (dfd, &delay))!=0){
                        printf ("ERROR %d\n",ret);
                        sprintf (response.strmsg, "ERROR %d\n",ret);
            } else {
                        sprintf (response.strmsg, "DONE");
     		}
     		response.status = ret;
     		response.data[0] = delay.settling_signal;
     		response.data[1] = delay.settling_reset;
     		response.data[2] = delay.clock_serial;
     		response.data[3] = delay.clock_sumwell;
    		response.data[4] = delay.clock_reset;
    		response.data[5] = delay.clock_parallel;
     		response.data[6] = delay.other1;
     		response.data[7] = delay.other2;
     		response.data[8] = delay.other3;
     		response.data[9] = delay.other4;
     		send (fdin, (void *)&response, sizeof (respstruct_t),0);
     		break;
         case LBNL_GET_PROG:
            printf ("cmd: GET_PROG\n");
			if ((ret=lbnl_readout_get_status (dfd, &readstat))!=0){
                     printf ("ERROR %d\n",ret);
                     sprintf (response.strmsg, "ERROR %d\n",ret);
            } else {
                     sprintf (response.strmsg, "DONE");
			}
		    response.status = ret;
		    response.data[0] = readstat.progress;
		    response.data[1] = readstat.rows_read;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
        case LBNL_GET_STAT:
            printf ("cmd: GET_STAT\n");
			if ((ret=lbnl_controller_get_status (dfd, &constat))!=0){
					printf ("ERROR %d\n",ret);
                    sprintf (response.strmsg, "ERROR %d\n",ret);
            } else {
                    sprintf (response.strmsg, "DONE");
			}
		    response.status = ret;
		    response.data[0] = constat.power_on;
		    response.data[1] = constat.ccd_idle;
		    response.data[2] = constat.clk_mask;
		    response.data[3] = constat.dac_mask;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
        case LBNL_DEFAUL_TIM:
            printf ("cmd: default_tim\ndata: %s\n",message.strmsg);
			if (strlen(message.strmsg) > 0){
//				sprintf (deftimpath, "%s", message.strmsg);
				sprintf (response.strmsg, "DONE");
				ret = 0;
			} else {
				ret = -22;
				sprintf (response.strmsg, "ERROR %d", ret);
			}
		    response.status = ret;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
       case LBNL_LOAD_TIM:
            printf ("cmd: Load_tim\ndata: %s\n",message.strmsg);
			if (strlen(message.strmsg) <= 0)
				sprintf (message.strmsg, "%s", DEFTIMPATH);
//			if (strcmp(message.strmsg,"default") == 0)
//				sprintf (message.strmsg, "%s", deftimpath);
			if ((ret=lbnl_controller_upload_timing (dfd, message.strmsg))!=0){
                       printf ("ERROR uploading %d\n",ret);
                       sprintf (response.strmsg, "ERROR %d\n",ret);
            } else {
					   printf ("Uploaded OK\n");
			}
		    response.status = ret;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
        case LBNL_SET_EXPT:
            printf ("cmd: SET_EXPT\ndata: %s\n",message.strmsg);
  			if (strlen(message.strmsg) <= 0){
  				printf ("ERROR %d\n",ret);
  				sprintf (response.strmsg, "ERROR %d\n",ret);
  			} else{
  				ret = 0;
  			}
  		    response.status = ret;
  			send (fdin, (void *)&response, sizeof (respstruct_t),0);
  			break;
        case LBNL_TEMPS:
            printf ("cmd: TEMPS\n");
			if ((ret=lbnl_controller_get_temps (dfd, &faux1, &faux2))!=0){
                     printf ("ERROR %d\n",ret);
                     sprintf (response.strmsg, "ERROR %d\n",ret);
            } else {
                     sprintf (response.strmsg, "DONE");
			}
		    response.status = ret;
//			faux1 = 22.5;
//			faux2 = 23.5;
		    *((float *) &response.data[0]) =  faux1;
		    *((float *) &response.data[1]) =  faux2;
			printf ("temp1 %f, temp2 %f\n", faux1, faux2);
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
        case LBNL_IDLE:
            printf ("cmd: IDLE %d\n", message.data[0]);
#if 1
			if ((ret=lbnl_ccd_idle (dfd, (i8) message.data[0]))<0){
                     printf ("ERROR %d\n",ret);
                     sprintf (response.strmsg, "ERROR %d\n",ret);
            } else {
                    sprintf (response.strmsg, "DONE");
			}
#endif
			ret = 0;
		    response.status = ret;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
        case LBNL_POWER:
            printf ("cmd: POWER %d\n", message.data[0]);
			printf ("dfd %d\n", dfd);
			if ((ret=lbnl_controller_power (dfd, message.data[0])) != 0){
				printf ("error setting power state");
				sprintf (response.strmsg, "ERROR %d\n",ret);
			    // lbnl_close (dfd);
			} else {
				if ( message.data[0] > 0 ){
					printf ("about to call init\n");
					if ((ret=lbnl_init (dfd))!=0){
						sprintf (response.strmsg, "ERROR initializing %d\n",ret);
					} else {
						printf ("cmd: POWER/INIT OK (ref %d)\n", dfd);
						sprintf (response.strmsg, "DONE");
					}
				}
			}
		    response.status = ret;
		    send (fdin, (void *)&response, sizeof (respstruct_t),0);
		    break;
        case LBNL_ENABLE:
            printf ("cmd: ENABLE 0x%x 0x%x\n", message.data[0], message.data[1]);
			if ((ret=lbnl_controller_enable (dfd, message.data[0], message.data[1]))!=0){
                      printf ("ERROR %d\n",ret);
                      sprintf (response.strmsg, "ERROR %d\n",ret);
            } else {
                      sprintf (response.strmsg, "DONE");
			}
		    response.status = ret;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
        case LBNL_GAIN:
            printf ("cmd: GAIN %d\n", message.data[0]);
			if ((ret=lbnl_controller_set_gain (dfd, message.data[0]))!=0){
                     printf ("ERROR %d\n",ret);
                     sprintf (response.strmsg, "ERROR %d\n",ret);
            } else {
                     sprintf (response.strmsg, "DONE");
			}
		    response.status = ret;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
        case LBNL_EXP_ADD:
            printf ("cmd: EXP_ADD %d\n", message.data[0]);
			if ((ret=lbnl_controller_set_start_address (dfd, message.data[0]))!=0){
                    printf ("ERROR %d\n",ret);
                    sprintf (response.strmsg, "ERROR %d\n",ret);
            } else {
                    sprintf (response.strmsg, "DONE");
			}
		    response.status = ret;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
       case LBNL_CCD_CLEAR:
            printf ("cmd: Clear\n");
			if ((ret=lbnl_ccd_clear (dfd))!=0){
                     printf ("ERROR %d\n",ret);
                     sprintf (response.strmsg, "ERROR %d\n",ret);
            } else
                     sprintf (response.strmsg, "DONE");
		    response.status = ret;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
       case LBNL_CCD_ERASE:
            printf ("cmd: Erase\n");
			if ((ret=lbnl_ccd_erase (dfd))!=0){
                     printf ("ERROR %d\n",ret);
                     sprintf (response.strmsg, "ERROR %d\n",ret);
            } else
                     sprintf (response.strmsg, "DONE");
		    response.status = ret;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
       case LBNL_CCD_PURGE:
            printf ("cmd: Purge\n");
			if ((ret=lbnl_ccd_purge (dfd))!=0){
                     printf ("ERROR %d\n",ret);
                     sprintf (response.strmsg, "ERROR clearing %d\n",ret);
            } else
                     sprintf (response.strmsg, "DONE");
		    response.status = ret;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
       case LBNL_IMAGE:
			nbytes = message.data[0];
            printf ("cmd: Image (%d bytes)\n", nbytes);
			response.status = 0;
			printf ("taking image\n");
			usleep (1000);
			if (artif_data==0){
			  if ((ret=lbnl_ccd_read (dfd, imbuffer))!=0){
                     printf ("ERROR acquiring %d\n",ret);
                     sprintf (response.strmsg, "ERROR acquiring %d\n",ret);
              } else {
                     printf ("image acquired, sending\n");
                     sprintf (response.strmsg, "DONE, image acquiered, sending\n");
              }
			} else {
				ret=lbnl_ccd_read_sim (dfd, imbuffer);
			}
            response.status = ret;
            send (fdin, (void *)&response, sizeof (respstruct_t),0);
            if (response.status == 0){
				sleep (1);
            	send (fdin, (char *)imbuffer, nbytes,0);
            }
			break;
       case LBNL_FITS:
			response.status = 0;
			printf ("taking image (buf 0x%lx) imbuffer[0] = %d\n", imbuffer, imbuffer[0]);
			usleep (1000);
			if ((ret=lbnl_ccd_read (dfd, imbuffer))!=0){
                         printf ("ERROR acquiring %d\n",ret);
                         sprintf (response.strmsg, "ERROR acquiring %d\n",ret);
            } else {
                         printf ("image acquired, writing\n");
                         if ((ret=lbnl_readout_get_fits (dfd, DEFFITSPATH, imbuffer)!=0)){
                                 	printf ("ERROR writing %d\n",ret);
                                  	sprintf (response.strmsg, "ERROR acquiring %d\n",ret);
                        	} else {
                                 	printf ("DONE\n");
                                 	sprintf (response.strmsg, "DONE");
                        	}
			}
			response.status = ret;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
       case LBNL_GET_DACS:
            printf ("cmd: GET_DACS\n");
			if ((ret=lbnl_controller_get_ndacs (dfd, &ndacs))<0){
                 printf ("ERROR %d\n",ret);
            } else {
				dacs = (dac_t *) malloc (ndacs *sizeof (dac_t));
				if ((ret=lbnl_controller_get_all_dacs (dfd, dacs, &ndacs))!=0){
                          printf ("ERROR %d\n",ret);
				}
//				pdebug ("daemon: dac[5] %d %f\n", dacs[5].address, dacs[5].tvalue);
			}
		    response.status = ret;
			sprintf (response.strmsg, "OK");
//			ret = send (fdin, (void *)&response, sizeof(respstruct_t),0);
//			printf ("response %d (sent %d)\n", response.status, ret);
			ret = 0;
			if (ret >= 0)
//				printf ("sending dacs\n");
//				sleep (1);
				if ((ret = send (fdin, dacs, ndacs*sizeof (dac_t),0)) == -1)
					printf ("error sending data %d\n", ret);
			break;
       case LBNL_GET_NDACS:
//          printf ("cmd: GET_NDACS\n");
			if ((ret=lbnl_controller_get_ndacs (dfd, &ndacs))<0){
                    printf ("ERROR %d\n",ret);
			}
			response.status = ret;
			response.data[0] = ndacs;
            printf ("resp: %d\n", response.data[0]);
			send (fdin, (void *)&response, sizeof(respstruct_t),0);
			break;
       case LBNL_SET_DAC:
			faux1 = *((float *) &message.data[1]);
            printf ("cmd: SET_DAC %d %f\n", message.data[0], faux1);
			if ((ret=lbnl_controller_set_dac_value (dfd, (u16) message.data[0], faux1))!=0){
                       printf ("ERROR %d\n",ret);
                       sprintf (response.strmsg, "ERROR %d\n",ret);
            } else {
                       sprintf (response.strmsg, "DONE");
			}
		    response.status = ret;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
      case LBNL_GET_OFF:
            printf ("cmd: GET_OFF\n");
			if ((ret=lbnl_controller_get_noffsets (dfd, &ndacs))<0){
                    printf ("ERROR %d\n",ret);
            } else {
					dacs = (dac_t *) malloc (ndacs *sizeof (dac_t));
					if ((ret=lbnl_controller_get_all_offsets (dfd, dacs, &ndacs))!=0){
                            printf ("ERROR %d\n",ret);
					}
					pdebug ("daemon: dac[0] %d %f\n", dacs[0].address, dacs[0].tvalue);
			}
		    response.status = ret;
			sprintf (response.strmsg, "OK");
//			ret = send (fdin, (void *)&response, sizeof(respstruct_t),0);
//			printf ("response %d (sent %d)\n", response.status, ret);
			ret = 0;
			if (ret >= 0)
//				printf ("sending dacs\n");
//				sleep (1);
				if ((ret = send (fdin, dacs, ndacs*sizeof (dac_t),0)) == -1)
					printf ("error sending data %d\n", ret);
			break;
       case LBNL_GET_NOFF:
//          printf ("cmd: GET_NOFF\n");
			if ((ret=lbnl_controller_get_noffsets (dfd, &ndacs))<0){
                     printf ("ERROR %d\n",ret);
			}
			response.status = ret;
			response.data[0] = ndacs;
            printf ("resp: %d\n", response.data[0]);
			send (fdin, (void *)&response, sizeof(respstruct_t),0);
			break;
                case LBNL_SET_OFF:
			faux1 = *((float *) &message.data[1]);
                       printf ("cmd: set_offset %d %f\n", message.data[0], faux1);
			if ((ret=lbnl_controller_set_offset_value (dfd, (u16) message.data[0], faux1))!=0){
                                 printf ("ERROR %d\n",ret);
                                  sprintf (response.strmsg, "ERROR %d\n",ret);
                        } else {
                                sprintf (response.strmsg, "DONE");	
			}
		       response.status = ret;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
         case LBNL_SET_CLK:
			faux1 = *((float *) &message.data[1]);
			faux2 = *((float *) &message.data[2]);
            printf ("cmd: SET_CLK %d %f %f\n", message.data[0], faux1, faux2);
			if ((ret=lbnl_controller_set_clk_value (dfd, (u16) message.data[0], faux1, faux2))!=0){
                      printf ("ERROR %d\n",ret);
                      sprintf (response.strmsg, "ERROR %d\n",ret);
            } else {
                      sprintf (response.strmsg, "DONE");
			}
		    response.status = ret;
			send (fdin, (void *)&response, sizeof (respstruct_t),0);
			break;
        case LBNL_GET_CLKS:
            printf ("cmd: GET_CLOCKS\n");
			if ((ret=lbnl_controller_get_nclocks (dfd, &ndacs))<0){
                printf ("ERROR %d\n",ret);
            } else {
				clocks = (lbnl_clock_t *) malloc (ndacs *sizeof (lbnl_clock_t));
				if ((ret=lbnl_controller_get_all_clocks (dfd, clocks, &ndacs))!=0){
                        printf ("ERROR %d\n",ret);
				}
//				pdebug ("daemon: dac[5] %d %f\n", dacs[5].address, dacs[5].tvalue);
			}
		        response.status = ret;
			sprintf (response.strmsg, "OK");
//			ret = send (fdin, (void *)&response, sizeof(respstruct_t),0);
//			printf ("response %d (sent %d)\n", response.status, ret);
			ret = 0;
			if (ret >= 0)
	//			printf ("sending clocks\n");
//				sleep (1);
				if ((ret = send (fdin, clocks, ndacs*sizeof (lbnl_clock_t),0)) == -1)
					printf ("error sending data %d\n", ret);
			break;
                case LBNL_GET_NCLKS:
 //                      printf ("cmd: GET_NCLOCKS\n");
			if ((ret=lbnl_controller_get_nclocks (dfd, &ndacs))<0){
                               	printf ("ERROR %d\n",ret);
			}
			response.status = ret;
			response.data[0] = ndacs;
			send (fdin, (void *)&response, sizeof(respstruct_t),0);
			break;
        case LBNL_SET_CPARS:
             printf ("cmd: SET_CPARS %d\n", message.data[0]);
             response.status = 0;
             if ((ret=lbnl_ccd_set_clear_params (dfd, message.data[0]))<0){
                      printf ("ERROR %d\n",ret);
                      response.status = ret;
             }
 		     sprintf (response.strmsg, "DONE");
 			 send (fdin, (void *)&response, sizeof (respstruct_t),0);
 			 break;
        case LBNL_GET_CPARS:
             printf ("cmd: GET_CPARS\n");
             if ((ret=lbnl_ccd_get_clear_params (dfd, &iaux1))<0){
                      printf ("ERROR %d\n",ret);
             }
             response.status = ret;
             response.data[0] = iaux1;
             send (fdin, (void *)&response, sizeof(respstruct_t),0);
             break;
         case LBNL_SET_EPARS:
             faux1 = *((float *) &message.data[0]);
             faux2 = *((float *) &message.data[1]);
             printf ("cmd: SET_EPARS %f %f %d %d\n", faux1, faux2, message.data[2],message.data[3]);
             response.status = 0;
             if ((ret=lbnl_ccd_set_erase_params (dfd, faux1, faux2, message.data[2], message.data[3]))<0){
                     printf ("ERROR %d\n",ret);
                     response.status = ret;
              }

 		     sprintf (response.strmsg, "DONE");
 			 send (fdin, (void *)&response, sizeof (respstruct_t),0);
 			 break;
          case LBNL_GET_EPARS:
             printf ("cmd: GET_CPARS\n");
             if ((ret=lbnl_ccd_get_erase_params (dfd, &faux1, &faux2, &iaux1, &iaux2))<0){
                               printf ("ERROR %d\n",ret);
             }
             response.status = ret;
             *((float *) &response.data[0]) =  faux1;
             *((float *) &response.data[1]) =  faux2;
             response.data[2] = iaux1;
             response.data[3] = iaux2;
             send (fdin, (void *)&response, sizeof(respstruct_t),0);
             break;
         case LBNL_SET_PPARS:
             faux1 = *((float *) &message.data[0]);
             printf ("cmd: SET_PPARS %f %d\n", faux1, message.data[1]);
             response.status = 0;
             if ((ret=lbnl_ccd_set_purge_params (dfd, faux1, message.data[1]))<0){
                      printf ("ERROR %d\n",ret);
                      response.status = ret;
             }

 		     sprintf (response.strmsg, "DONE");
 			 send (fdin, (void *)&response, sizeof (respstruct_t),0);
 			 break;
        case LBNL_GET_PPARS:
            printf ("cmd: GET_PPARS\n");
            if ((ret=lbnl_ccd_get_purge_params (dfd, &faux1, &iaux1))<0){
                   printf ("ERROR %d\n",ret);
            }
            response.status = ret;
            *((float *) &response.data[0]) =  faux1;
            response.data[1] = iaux1;
            send (fdin, (void *)&response, sizeof(respstruct_t),0);
            break;
		case LBNL_SHUTDOWN:
			printf ("received SHUTDOWN\n");
			got_sigterm=1;
			close (fdin);
			fdin = 0;
			cin = 0;
			close (listenfd);
			break;
		default:
			sprintf (response.strmsg, "ERROR unknown cmd %d\n",message.cmd);
			response.status = -EINVAL;
			response.data[0] = response.status;
			send (fdin, (void *)&response, sizeof (response),0);
			break;
		
	}
     }
    } while (cin>0);

  if (fdin != 0)
  	close(fdin);

  printf ("client terminated\n");
  if (dfd != 0) {
	  lbnl_close (dfd);
	  printf ("cmd: CLOSE\n");
	  dfd = 0;
  }
  // sleep (1);
  cin = 0;
  return(NULL);
  }

void signal_handler(int sig) {
  switch(sig) {
  case SIGHUP:
    syslog(LOG_INFO, "hangup signal catched");
    break;
  case SIGTERM:
    syslog(LOG_INFO, "terminate signal catched");
    got_sigterm=1;
    break;
        }
}

