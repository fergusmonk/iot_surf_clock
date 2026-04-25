#pragma once
#include <string>
#include <vector>

// Wraps whisper.cpp (or PocketSphinx) for speech-to-text
class Voice {
public:
    // Transcribe PCM samples to text
    virtual std::string transcribe(const std::vector<float>& pcm) = 0;
    virtual ~Voice() = default;
};
