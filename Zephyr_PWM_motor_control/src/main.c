#include <zephyr/kernel.h>
#include <zephyr/drivers/pwm.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/usb/usb_device.h>
#include <zephyr/logging/log.h>
#include <stdlib.h>
#include <string.h>

LOG_MODULE_REGISTER(main, LOG_LEVEL_INF);

static const struct pwm_dt_spec vibro_pwm = PWM_DT_SPEC_GET(DT_ALIAS(vibropwm));
static const struct device *usb_uart = DEVICE_DT_GET_ONE(zephyr_cdc_acm_uart);

static uint32_t current_freq = 5000;
static uint32_t current_duty = 50;
static bool motor_enabled = false;

#define RX_BUF_SIZE 64
static char rx_buf[RX_BUF_SIZE];
static int rx_buf_pos = 0;

void update_motor(void) {
    if (!motor_enabled || current_duty == 0 || current_freq == 0) {
        pwm_set_dt(&vibro_pwm, 0, 0);
        LOG_INF("Status: WYLACZONY");
        return;
    }

    if (current_duty > 100) current_duty = 100;

    uint32_t period_ns = 1000000000UL / current_freq;
    uint32_t pulse_ns = (period_ns * current_duty) / 100;

    pwm_set_dt(&vibro_pwm, period_ns, pulse_ns);
    LOG_INF("Status: WLACZONY | Freq: %u Hz | Duty: %u %%", current_freq, current_duty);
}

void process_command(const char *cmd) {
    if (strlen(cmd) < 3) return;

    if (cmd[0] == 'D' && cmd[1] == ':') {
        current_duty = atoi(&cmd[2]);
    } else if (cmd[0] == 'F' && cmd[1] == ':') {
        current_freq = atoi(&cmd[2]);
    } else if (cmd[0] == 'E' && cmd[1] == ':') {
        motor_enabled = (atoi(&cmd[2]) != 0);
    }
    
    update_motor();
}

static void uart_interrupt_handler(const struct device *dev, void *user_data) {
    uart_irq_update(dev);

    if (uart_irq_rx_ready(dev)) {
        int data_length;
        uint8_t c;

        while ((data_length = uart_fifo_read(dev, &c, 1)) > 0) {
            if (c == '\n' || c == '\r') {
                if (rx_buf_pos > 0) {
                    rx_buf[rx_buf_pos] = '\0';
                    process_command(rx_buf);
                    rx_buf_pos = 0; 
                }
            } else if (rx_buf_pos < RX_BUF_SIZE - 1) {
                rx_buf[rx_buf_pos++] = c;
            }
        }
    }
}

int main(void) {
    if (!pwm_is_ready_dt(&vibro_pwm)) {
        LOG_ERR("Blad: PWM nie jest gotowe!");
        return 0;
    }

    if (!device_is_ready(usb_uart)) {
        LOG_ERR("Blad: USB UART nie jest gotowe! Czy wezel cdc-acm jest w overlay?");
        return 0;
    }

    /* Inicjalizacja stosu USB Zephyra */
    int ret = usb_enable(NULL);
    if (ret != 0) {
        LOG_ERR("Blad inicjalizacji USB!");
        return 0;
    }

    uart_irq_callback_set(usb_uart, uart_interrupt_handler);
    uart_irq_rx_enable(usb_uart);

    LOG_INF("System USB gotowy. Czekam na komendy z aplikacji w Pythonie...");
    update_motor(); 

    while (1) {
        k_msleep(1000); 
    }
    return 0;
}