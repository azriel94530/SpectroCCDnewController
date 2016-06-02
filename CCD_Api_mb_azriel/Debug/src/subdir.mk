################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../src/RTDmath.c \
../src/lbnlLib.c \
../src/lbnl_mem.c \
../src/lbnl_parser.c \
../src/lbnl_spi.c 

OBJS += \
./src/RTDmath.o \
./src/lbnlLib.o \
./src/lbnl_mem.o \
./src/lbnl_parser.o \
./src/lbnl_spi.o 

C_DEPS += \
./src/RTDmath.d \
./src/lbnlLib.d \
./src/lbnl_mem.d \
./src/lbnl_parser.d \
./src/lbnl_spi.d 


# Each subdirectory must supply rules for building sources it contributes
src/%.o: ../src/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: ARM Linux gcc compiler'
	arm-xilinx-linux-gnueabi-gcc -Wall -O0 -g3 -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


