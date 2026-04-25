#pragma once

// Abstract GPIO interface — swap real/mock at compile time via USE_MOCK_HAL
class GPIO {
public:
    virtual void write(int pin, bool high) = 0;
    virtual bool read(int pin) = 0;
    virtual ~GPIO() = default;
};

#ifdef USE_MOCK_HAL
#include "gpio_mock.hpp"
using GPIOImpl = GPIOMock;
#else
#include "gpio_real.hpp"
using GPIOImpl = GPIOReal;
#endif
