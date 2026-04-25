#pragma once
#include "gpio.hpp"
#include <iostream>

class GPIOMock : public GPIO {
public:
    void write(int pin, bool high) override {
        std::cout << "[MOCK GPIO] pin " << pin << " -> " << (high ? "HIGH" : "LOW") << "\n";
    }

    bool read(int pin) override {
        std::cout << "[MOCK GPIO] read pin " << pin << " -> 0 (stub)\n";
        return false;
    }
};
