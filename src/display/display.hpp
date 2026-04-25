#pragma once
#include <string>

// 7-segment display interface
class Display {
public:
    virtual void showTime(int hour, int minute) = 0;
    virtual void showText(const std::string& text) = 0;
    virtual void clear() = 0;
    virtual ~Display() = default;
};
