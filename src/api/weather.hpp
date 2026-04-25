#pragma once
#include <string>

struct WeatherData {
    float tempC;
    std::string condition;
    int humidity;
};

// Fetch current weather from an external API (e.g. Open-Meteo — free, no key needed)
class WeatherClient {
public:
    virtual WeatherData fetch(const std::string& location) = 0;
    virtual ~WeatherClient() = default;
};
