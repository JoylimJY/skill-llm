import os
import random

random.seed(42)

# Create deeply nested project structure with distractor files
dirs = [
    "robot_arm_fw/src/drivers",
    "robot_arm_fw/src/app",
    "robot_arm_fw/src/rtos",
    "robot_arm_fw/src/hal",
    "robot_arm_fw/include/drivers",
    "robot_arm_fw/include/app",
    "robot_arm_fw/config",
    "robot_arm_fw/tools",
    "robot_arm_fw/tests",
    "robot_arm_fw/docs",
    "robot_arm_fw/bootloader",
    "robot_arm_fw/scripts",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# ---- Distractor files ----

# 1. Stale/incorrect motor driver with wrong prescaler values (distractor)
with open("robot_arm_fw/src/drivers/motor_old.c", "w") as f:
    f.write("""\
// DEPRECATED - do not use
#include "motor_old.h"

void Motor_Init_Bad(void) {
    // Wrong: uses 36MHz assumption, incorrect ARR
    // TIM_Period = 1000 - 1;  // ARR
    // TIM_Prescaler = 36 - 1; // PSC - WRONG for 72MHz
}

void Motor_SetSpeed_Bad(uint8_t speed) {
    // Wrong formula
    TIM3->CCR2 = speed * 10;  // INCORRECT
}
""")

# 2. Distractor HAL GPIO file
with open("robot_arm_fw/src/hal/gpio.c", "w") as f:
    f.write("""\
#include "gpio.h"
#include "stm32f10x.h"

void GPIO_Init_All(void) {
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA | RCC_APB2Periph_GPIOB, ENABLE);
    GPIO_InitTypeDef GPIO_InitStructure;
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOB, &GPIO_InitStructure);
}

void GPIO_LED_Toggle(void) {
    GPIOB->ODR ^= (1 << 0);
}
""")

# 3. Distractor I2C sensor driver
with open("robot_arm_fw/src/drivers/i2c_sensor.c", "w") as f:
    f.write("""\
#include "i2c_sensor.h"

#define MPU6050_ADDR  0x68

void MPU6050_Init(void) {
    I2C_WriteReg(MPU6050_ADDR, 0x6B, 0x00); // Wake up
    I2C_WriteReg(MPU6050_ADDR, 0x1B, 0x08); // Gyro FS=500
}

void MPU6050_ReadAccel(int16_t *ax, int16_t *ay, int16_t *az) {
    uint8_t buf[6];
    for (int i = 0; i < 6; i++)
        buf[i] = I2C_ReadReg(MPU6050_ADDR, 0x3B + i);
    *ax = (int16_t)((buf[0] << 8) | buf[1]);
    *ay = (int16_t)((buf[2] << 8) | buf[3]);
    *az = (int16_t)((buf[4] << 8) | buf[5]);
}
""")

# 4. Distractor CAN bus driver
with open("robot_arm_fw/src/drivers/can_bus.c", "w") as f:
    f.write("""\
#include "can_bus.h"

void CAN_Init_500kbps(void) {
    CAN_InitTypeDef CAN_InitStructure;
    CAN_InitStructure.CAN_Prescaler = 4;
    CAN_InitStructure.CAN_BS1 = CAN_BS1_9tq;
    CAN_InitStructure.CAN_BS2 = CAN_BS2_8tq;
    CAN_Init(CAN1, &CAN_InitStructure);
}
""")

# 5. Distractor SPI flash driver
with open("robot_arm_fw/src/drivers/spi_flash.c", "w") as f:
    f.write("""\
#include "spi_flash.h"

#define FLASH_CS_LOW()   GPIOA->BRR  = (1 << 4)
#define FLASH_CS_HIGH()  GPIOA->BSRR = (1 << 4)

uint8_t SPI_Flash_ReadID(void) {
    FLASH_CS_LOW();
    SPI_SendByte(0x9F);
    uint8_t id = SPI_RecvByte();
    FLASH_CS_HIGH();
    return id;
}
""")

# 6. Distractor FreeRTOS config (wrong stack sizes, wrong priorities)
with open("robot_arm_fw/config/FreeRTOSConfig_old.h", "w") as f:
    f.write("""\
/* OBSOLETE FreeRTOS Config - Do Not Use */
#define configUSE_PREEMPTION         0   // WRONG - should be 1
#define configCPU_CLOCK_HZ           ( ( unsigned long ) 8000000 )  // WRONG - 8MHz not 72MHz
#define configTICK_RATE_HZ           ( ( TickType_t ) 100 )  // WRONG - should be 1000
#define configMAX_PRIORITIES         ( 5 )
#define configMINIMAL_STACK_SIZE     ( ( unsigned short ) 64 )  // too small
#define configTOTAL_HEAP_SIZE        ( ( size_t ) ( 1 * 1024 ) )
""")

# 7. Distractor UART polling (not interrupt-based)
with open("robot_arm_fw/src/drivers/uart_poll.c", "w") as f:
    f.write("""\
#include "uart_poll.h"

// Polling mode - DEPRECATED, use interrupt mode instead
uint8_t UART_PollRead(void) {
    while (!(USART1->SR & USART_SR_RXNE));
    return (uint8_t)(USART1->DR & 0xFF);
}

void UART_PollWrite(uint8_t byte) {
    while (!(USART1->SR & USART_SR_TXE));
    USART1->DR = byte;
}
""")

# 8. Distractor state machine skeleton (incomplete)
with open("robot_arm_fw/src/app/state_machine_stub.c", "w") as f:
    f.write("""\
#include "state_machine.h"

typedef enum {
    STATE_IDLE,
    STATE_RUNNING,
    STATE_ERROR,
    STATE_ESTOP,
} RobotState_t;

// TODO: implement transitions
RobotState_t current_state = STATE_IDLE;

void StateMachine_Update(void) {
    // not implemented
}
""")

# 9. Distractor Makefile fragment
with open("robot_arm_fw/Makefile", "w") as f:
    f.write("""\
TARGET = robot_arm_fw
MCU = cortex-m3
CC = arm-none-eabi-gcc
CFLAGS = -mcpu=$(MCU) -mthumb -O2 -Wall
LDFLAGS = -T linker.ld -nostartfiles

SRC = $(wildcard src/**/*.c)
OBJ = $(SRC:.c=.o)

all: $(TARGET).elf

$(TARGET).elf: $(OBJ)
\t$(CC) $(LDFLAGS) -o $@ $^

%.o: %.c
\t$(CC) $(CFLAGS) -c -o $@ $^

clean:
\trm -f $(OBJ) $(TARGET).elf
""")

# 10. Distractor linker script
with open("robot_arm_fw/linker.ld", "w") as f:
    f.write("""\
MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 256K
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 48K
}

SECTIONS
{
    .text : { *(.text*) } > FLASH
    .data : { *(.data*) } > RAM AT > FLASH
    .bss  : { *(.bss*)  } > RAM
}
""")

# 11. Distractor OTA stub
with open("robot_arm_fw/bootloader/ota_stub.c", "w") as f:
    f.write("""\
#include "ota.h"

#define APP_START_ADDR  0x08004000
#define BOOTLOADER_SIZE (16 * 1024)

void OTA_JumpToApp(void) {
    typedef void (*pFunction)(void);
    uint32_t JumpAddress = *(__IO uint32_t*)(APP_START_ADDR + 4);
    pFunction Jump = (pFunction)JumpAddress;
    __set_MSP(*(__IO uint32_t*)APP_START_ADDR);
    Jump();
}
""")

# 12. Distractor ADC driver
with open("robot_arm_fw/src/drivers/adc.c", "w") as f:
    f.write("""\
#include "adc.h"

uint16_t ADC_ReadChannel(uint8_t channel) {
    ADC1->SQR3 = channel;
    ADC1->CR2 |= ADC_CR2_SWSTART;
    while (!(ADC1->SR & ADC_SR_EOC));
    return ADC1->DR;
}
""")

# 13. Distractor tools script
with open("robot_arm_fw/tools/flash.sh", "w") as f:
    f.write("""\
#!/bin/bash
# Flash firmware via ST-Link
openocd -f interface/stlink.cfg -f target/stm32f1x.cfg \\
    -c "program robot_arm_fw.elf verify reset exit"
""")

# 14. Distractor test file
with open("robot_arm_fw/tests/test_pwm_mock.c", "w") as f:
    f.write("""\
#include <assert.h>
#include <stdint.h>

// Mock CCR2 register
uint32_t mock_CCR2 = 0;

void Motor_SetSpeed_test(uint8_t speed) {
    // This uses a WRONG formula for testing purposes (intentionally broken)
    mock_CCR2 = speed * 15;  // WRONG multiplier, just a placeholder
}

int main(void) {
    Motor_SetSpeed_test(50);
    // assert(mock_CCR2 == 1000);  // Would fail with wrong formula
    return 0;
}
""")

# 15. Requirements spec (business language, no technical hints)
with open("robot_arm_fw/docs/requirements.txt", "w") as f:
    f.write("""\
Robot Arm Motor Controller - Firmware Requirements
===================================================
Platform: STM32F103RCT6 (72MHz system clock, AHB/APB2 = 72MHz, APB1 = 36MHz)
Motor: DC brushed motor, controlled via PWM signal at 50Hz standard servo frequency
Speed range: 0% to 100% (maps to hardware timer compare register)
Command interface: UART at 115200 baud, interrupt-driven receiver
Command format: ASCII, e.g. "SPEED:75\r\n" sets motor to 75%
Task isolation: Motor control and UART receive must run as separate RTOS tasks
Inter-task communication: Speed commands passed via message queue, blocking mode
PWM output pin: PB5 (Timer 3, Channel 2)
Idle/neutral position: 75% duty cycle (servo neutral)
Stack sizes: per embedded best practices for Cortex-M3

Deliverable: A single self-contained C source file implementing the complete firmware module.
""")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("robot_arm_fw"):
    for file in files:
        print(f"  {os.path.join(root, file)}")