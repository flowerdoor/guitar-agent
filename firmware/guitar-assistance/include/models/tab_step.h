#pragma once
#include <stdint.h>
#include <stddef.h>

namespace ScoreModel {
    constexpr size_t STRING_COUNT = 6;
    constexpr int8_t NO_NOTE =-1;
    constexpr int8_t MUTED =-2;
    constexpr uint16_t TICKS_PER_BEAT = 480;


    struct TabStep {
        uint32_t startTick;
        uint32_t durationTicks;

        int8_t frets[STRING_COUNT];
        uint16_t bar;
        uint8_t beat;
    };
}