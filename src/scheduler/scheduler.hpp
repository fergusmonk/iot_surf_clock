#pragma once
#include <atomic>
#include <functional>
#include <string>
#include <vector>

enum class AlarmRepeat {
    Once,    // fires once then removes itself
    Daily,   // fires every day at the same time
};

struct AlarmEntry {
    int hour;
    int minute;
    std::string label;            // e.g. "wakeup", "bedtime"
    AlarmRepeat repeat = AlarmRepeat::Daily;
    std::function<void()> action;
};

// Returns true if the alarm should fire at the given hour/minute
inline bool alarmMatches(const AlarmEntry& alarm, int hour, int minute) {
    return alarm.hour == hour && alarm.minute == minute;
}

// In-process scheduler backed by system clock (NTP-synced via OS)
class Scheduler {
public:
    void addAlarm(AlarmEntry entry);
    void removeAlarm(const std::string& label);
    void start();  // spawns background thread
    void stop();

private:
    void loop();
    void sleepUntilNextMinute();

    std::vector<AlarmEntry> alarms_;
    std::atomic<bool> running_{false};
    int lastFiredMinute_ = -1;  // prevents double-firing within the same minute
};
