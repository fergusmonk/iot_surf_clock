# IoT Alarm Clock — C++ Architecture

## Hardware Target
**Raspberry Pi Zero 2w** (ARM Cortex-A53, 512MB RAM, Linux)

---

## Project Structure

```
iot_assistant/
├── CMakeLists.txt
├── src/
│   ├── main.cpp
│   ├── hal/                  # Hardware Abstraction Layer
│   │   ├── gpio.hpp          # Interface
│   │   ├── gpio_real.cpp     # pigpio implementation
│   │   └── gpio_mock.cpp     # Mock for dev without hardware
│   ├── display/              # 7-segment display driver
│   ├── relay/                # Light relay control
│   ├── audio/                # Mic/speaker interface
│   ├── api/                  # External API clients
│   ├── scheduler/            # Alarm / cron logic
│   └── voice/                # Voice command processing
├── tests/
└── third_party/              # Vendored or fetched deps
```

---

## Build System

| Tool | Purpose |
|------|---------|
| **CMake** (3.16+) | Build configuration — standard for C++ projects |
| **Ninja** | Fast build backend (`cmake -G Ninja`) |
| **vcpkg** | C++ package manager for dependencies ( use triplets for cross compiling )|

### Cross-compilation (optional)
Compile on your dev machine targeting ARM instead of building on the Pi (which is slow):
```
sudo apt install gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf
```
Or just compile natively on the Pi via SSH while you're prototyping — simpler to start.

---

## Libraries

### GPIO
| Library | Notes |
|---------|-------|
| **pigpio** | Best option for Pi — supports hardware PWM, I2C, SPI, callbacks. Requires daemon (`pigpiod`) |

```bash
sudo apt install libpigpio-dev
```

### 7-Segment Display
Depends on how the display is wired:
| Wiring | Library |
|--------|---------|
| Direct GPIO (common anode/cathode) | pigpio GPIO writes |
| I2C (TM1637 chip) | **tm1637** (header-only, include directly) |
| SPI | pigpio SPI functions |

### Relay
No extra library needed — a single GPIO output via pigpio.

### Audio
| Library | Purpose |
|---------|---------|
| **ALSA** (`libasound2-dev`) | Low-level Linux audio — mic input and speaker output |
| **PortAudio** | Cross-platform audio I/O — easier API, good for dev/mock on desktop |

### Voice Recognition
| Library | Notes |
|---------|-------|
| **whisper.cpp** | Runs on-device, no internet needed. Quantised models fit on Pi Zero 2w. Best accuracy. |
| **PocketSphinx** | Lighter, faster but less accurate — fallback option |

### Text-to-Speech
| Library | Notes |
|---------|-------|
| **espeak-ng** | `system("espeak-ng '...'")` or via its C API — lightweight, runs on Pi |
| **piper** | Neural TTS, better quality, heavier |

### HTTP / API Clients
| Library | Notes |
|---------|-------|
| **cpp-httplib** | Header-only, no deps — simplest option for GET/POST |
| **libcurl** | More powerful, widely documented, C API with C++ wrappers |

Recommendation: start with **cpp-httplib** (just drop in a header), switch to libcurl if you need more control.

### JSON Parsing
| Library | Notes |
|---------|-------|
| **nlohmann/json** | Header-only, intuitive API — `json["temp"].get<float>()` |

```bash
# via vcpkg
vcpkg install nlohmann-json
```

### HTTP Server (for home server API)
| Library | Notes |
|---------|-------|
| **cpp-httplib** | Also serves HTTP — same library as client |
| **Crow** | Lightweight REST microframework if you need routing |

cpp-httplib can do both client and server, so start there.

### Scheduling / Alarms
| Approach | Notes |
|----------|-------|
| **std::thread + std::chrono** | Simple in-process scheduler — sufficient for alarms |
| **libcron** | Full cron expression parsing in C++ if you need cron syntax |
| **system cron** | Shell calls your binary — simpler but less control |

Recommendation: `std::thread` + a small in-process scheduler to start.

---

## HAL (Hardware Abstraction Layer)

The key pattern for developing without hardware:

```cpp
// hal/gpio.hpp
class GPIO {
public:
    virtual void write(int pin, bool high) = 0;
    virtual bool read(int pin) = 0;
    virtual ~GPIO() = default;
};
```

```cpp
// hal/gpio_real.cpp  — uses pigpio
// hal/gpio_mock.cpp  — prints to stdout
```

Select via CMake option or environment variable:
```bash
cmake -DUSE_MOCK_HAL=ON ..   # dev machine
cmake -DUSE_MOCK_HAL=OFF ..  # Pi
```

---

## Testing

| Tool | Purpose |
|------|---------|
| **GoogleTest** | Unit tests — test scheduling logic, API parsing, etc. |
| **GoogleMock** | Mock the HAL interfaces |

```bash
vcpkg install gtest
```

---

## Development Workflow (No Hardware)

1. Build with `USE_MOCK_HAL=ON` — GPIO writes print to terminal
2. Render 7-segment display state as ASCII in mock
3. All API, scheduling, and voice logic runs natively on your machine
4. When Pi arrives: swap `USE_MOCK_HAL=OFF`, deploy binary via `scp`, done

---

## Dependency Summary

```bash
# On Pi / Debian-based dev machine
sudo apt install \
    cmake ninja-build \
    libpigpio-dev \
    libasound2-dev \
    libportaudio2 portaudio19-dev \
    espeak-ng libespeak-ng-dev

# Via vcpkg
vcpkg install nlohmann-json gtest
# cpp-httplib and whisper.cpp — clone directly (header-only / submodule)
```
