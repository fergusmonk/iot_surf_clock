#pragma once
#include "audio.hpp"
#include <iostream>

class AudioMock : public Audio {
public:
    std::vector<float> capture(int durationMs) override {
        std::cout << "[AUDIO] capture stub (" << durationMs << "ms)\n";
        return {};
    }

    void speak(const std::string& text) override {
        std::cout << "[AUDIO] speak: \"" << text << "\"\n";
    }
};
