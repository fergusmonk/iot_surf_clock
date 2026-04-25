#pragma once
#include "display.hpp"
#include <iostream>
#include <iomanip>

class DisplayMock : public Display {
public:
    void showTime(int hour, int minute) override {
        std::cout << "[DISPLAY] "
                  << std::setw(2) << std::setfill('0') << hour << ":"
                  << std::setw(2) << std::setfill('0') << minute << "\n";
    }

    void showText(const std::string& text) override {
        std::cout << "[DISPLAY] " << text << "\n";
    }

    void clear() override {
        std::cout << "[DISPLAY] cleared\n";
    }
};
