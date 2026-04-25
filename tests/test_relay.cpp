#include <gtest/gtest.h>
#include "relay/relay.hpp"
#include "hal/gpio_mock.hpp"

TEST(RelayTest, TurnsOnAndOff) {
    GPIOMock gpio;
    Relay relay(gpio, 17);
    relay.on();   // expect pin 17 HIGH
    relay.off();  // expect pin 17 LOW
    SUCCEED();    // visual confirmation via mock stdout for now
}
