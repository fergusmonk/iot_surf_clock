#ifndef USE_MOCK_HAL
#include "gpio_real.hpp"
// #include <pigpio.h>

GPIOReal::GPIOReal() {
    // gpioInitialise();
}

GPIOReal::~GPIOReal() {
    // gpioTerminate();
}

void GPIOReal::write(int pin, bool high) {
    // gpioWrite(pin, high ? 1 : 0);
}

bool GPIOReal::read(int pin) {
    // return gpioRead(pin) == 1;
    return false;
}
#endif
