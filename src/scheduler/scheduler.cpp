#include "scheduler.hpp"
#include <algorithm>
#include <chrono>
#include <ctime>
#include <iostream>
#include <thread>

void Scheduler::addAlarm(AlarmEntry entry) {
    alarms_.push_back(std::move(entry));
}

void Scheduler::removeAlarm(const std::string& label) {
    alarms_.erase(
        std::remove_if(alarms_.begin(), alarms_.end(),
            [&](const AlarmEntry& e) { return e.label == label; }),
        alarms_.end());
}

void Scheduler::start() {
    running_ = true;
    std::thread(&Scheduler::loop, this).detach();
}

void Scheduler::stop() {
    running_ = false;
}

void Scheduler::loop() {
    while (running_) {
        auto now = std::time(nullptr);
        auto* t  = std::localtime(&now);

        // Unique key for this minute — avoids double-firing if we wake slightly early
        int minuteKey = t->tm_hour * 60 + t->tm_min;

        if (minuteKey != lastFiredMinute_) {
            std::vector<std::string> toRemove;

            for (auto& alarm : alarms_) {
                if (t->tm_hour == alarm.hour && t->tm_min == alarm.minute) {
                    std::cout << "[SCHEDULER] firing: " << alarm.label << "\n";
                    alarm.action();

                    if (alarm.repeat == AlarmRepeat::Once)
                        toRemove.push_back(alarm.label);
                }
            }

            for (auto& label : toRemove)
                removeAlarm(label);

            lastFiredMinute_ = minuteKey;
        }

        sleepUntilNextMinute();
    }
}

void Scheduler::sleepUntilNextMinute() {
    using namespace std::chrono;

    // Calculate seconds remaining until the next minute boundary
    auto now     = system_clock::now();
    auto nowSecs = duration_cast<seconds>(now.time_since_epoch()).count();
    auto secsUntilNextMinute = 60 - (nowSecs % 60);

    // Cap at 60s — wake slightly early (at 58s) to avoid sleeping past the boundary
    auto sleepFor = seconds(std::min<long>(secsUntilNextMinute, 58));
    std::this_thread::sleep_for(sleepFor);
}
