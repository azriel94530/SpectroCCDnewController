################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../src/daemon/lbnl_daemon.c 

OBJS += \
./src/daemon/lbnl_daemon.o 

C_DEPS += \
./src/daemon/lbnl_daemon.d 


# Each subdirectory must supply rules for building sources it contributes
src/daemon/%.o: ../src/daemon/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: ARM Linux gcc compiler'
	arm-xilinx-linux-gnueabi-gcc -Wall -O0 -g3 -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

