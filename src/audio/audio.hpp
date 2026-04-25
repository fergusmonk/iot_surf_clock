#pragma once
#include <string>
#include <vector>

// Audio interface for mic input and speaker output
class Audio {
public:
    // Capture audio from microphone, return raw PCM samples
    virtual std::vector<float> capture(int durationMs) = 0;

    // Play a WAV file or TTS string via espeak-ng
    virtual void speak(const std::string& text) = 0;

    virtual ~Audio() = default;
};
