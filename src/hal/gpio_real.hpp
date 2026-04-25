#pragma once
#include "gpio.hpp"
// #include <pigpio.h>  // uncomment when building on Pi

class GPIOReal : public GPIO {
public:
    GPIOReal();
    ~GPIOReal() override;

    void write(int pin, bool high) override;
    bool read(int pin) override;
};
