#pragma once
#include "hal/gpio.hpp"

// Controls a single relay (e.g. bedside light)
class Relay {
public:
    Relay(GPIO& gpio, int pin) : gpio_(gpio), pin_(pin) {}

    void on()  { gpio_.write(pin_, true); }
    void off() { gpio_.write(pin_, false); }

private:
    GPIO& gpio_;
    int pin_;
};
