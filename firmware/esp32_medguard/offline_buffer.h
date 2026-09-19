#ifndef OFFLINE_BUFFER_H
#define OFFLINE_BUFFER_H

#include <Arduino.h>
#include "config.h"

// Struct for a single sensor snapshot
struct TelemetryRecord {
    unsigned long timestamp_sec;
    float temperature;
    float humidity;
    int light_adc;
    bool door_open;
    bool power_connected;
    float battery_v;
};

class OfflineRingBuffer {
private:
    TelemetryRecord buffer[MAX_OFFLINE_RECORDS];
    int head = 0;
    int tail = 0;
    int count = 0;
    bool is_overflowed = false;

public:
    OfflineRingBuffer() {}

    bool push(const TelemetryRecord& record) {
        buffer[head] = record;
        head = (head + 1) % MAX_OFFLINE_RECORDS;
        
        if (count < MAX_OFFLINE_RECORDS) {
            count++;
            return true;
        } else {
            // Buffer full: drop oldest record
            tail = (tail + 1) % MAX_OFFLINE_RECORDS;
            is_overflowed = true;
            return false;
        }
    }

    bool pop(TelemetryRecord& record) {
        if (count == 0) return false;
        record = buffer[tail];
        tail = (tail + 1) % MAX_OFFLINE_RECORDS;
        count--;
        return true;
    }

    bool peek(int index, TelemetryRecord& record) const {
        if (index < 0 || index >= count) return false;
        int actual_idx = (tail + index) % MAX_OFFLINE_RECORDS;
        record = buffer[actual_idx];
        return true;
    }

    int size() const {
        return count;
    }

    bool isEmpty() const {
        return count == 0;
    }

    bool isFull() const {
        return count >= MAX_OFFLINE_RECORDS;
    }

    void clear() {
        head = 0;
        tail = 0;
        count = 0;
        is_overflowed = false;
    }

    bool hasOverflowed() const {
        return is_overflowed;
    }
};

#endif // OFFLINE_BUFFER_H
