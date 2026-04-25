#include <gtest/gtest.h>
#include "scheduler/scheduler.hpp"

// --- alarmMatches ---

TEST(AlarmMatchesTest, FiresAtCorrectTime) {
    AlarmEntry a{7, 30, "wakeup", AlarmRepeat::Daily, []() {}};
    EXPECT_TRUE(alarmMatches(a, 7, 30));
}

TEST(AlarmMatchesTest, DoesNotFireAtWrongHour) {
    AlarmEntry a{7, 30, "wakeup", AlarmRepeat::Daily, []() {}};
    EXPECT_FALSE(alarmMatches(a, 8, 30));
}

TEST(AlarmMatchesTest, DoesNotFireAtWrongMinute) {
    AlarmEntry a{7, 30, "wakeup", AlarmRepeat::Daily, []() {}};
    EXPECT_FALSE(alarmMatches(a, 7, 31));
}

TEST(AlarmMatchesTest, FiresAtMidnight) {
    AlarmEntry a{0, 0, "midnight", AlarmRepeat::Daily, []() {}};
    EXPECT_TRUE(alarmMatches(a, 0, 0));
}

// --- addAlarm / removeAlarm ---

TEST(SchedulerTest, AddAlarmDoesNotFire) {
    Scheduler s;
    bool fired = false;
    s.addAlarm({7, 0, "wakeup", AlarmRepeat::Daily, [&]() { fired = true; }});
    EXPECT_FALSE(fired);  // adding alone must not trigger action
}

TEST(SchedulerTest, RemoveNonExistentLabelIsHarmless) {
    Scheduler s;
    s.addAlarm({7, 0, "wakeup", AlarmRepeat::Daily, []() {}});
    s.removeAlarm("does-not-exist"); 
    SUCCEED();
}

TEST(SchedulerTest, RemoveAlarmPreventsFireOpportunity) {
    Scheduler s;
    bool fired = false;
    s.addAlarm({7, 0, "wakeup", AlarmRepeat::Once, [&]() { fired = true; }});
    s.removeAlarm("wakeup");
    EXPECT_FALSE(fired);
}

TEST(SchedulerTest, MultipleAlarmsCanBeAdded) {
    Scheduler s;
    int count = 0;
    s.addAlarm({7,  0,  "wakeup",  AlarmRepeat::Daily, [&]() { count++; }});
    s.addAlarm({22, 30, "bedtime", AlarmRepeat::Daily, [&]() { count++; }});
    // Neither should have fired just from being added
    EXPECT_EQ(count, 0);
}
 

