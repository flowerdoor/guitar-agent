#pragma once

#include <stddef.h>
#include <stdint.h>
//一次触摸读取产生的状态
struct TouchState{
    bool touched;
    bool justPressed;
    bool justReleased;

    int16_t x;
    int16_t y;

    int16_t startX;
    int16_t startY;
};

class TouchDriver {
public:
    TouchDriver();

    bool begin();
    //读取当前触摸状态
    TouchState read();

private:
    bool readRegister(
        uint8_t reg,
        uint8_t &value
    );
    bool readRegisters(
        uint8_t reg,
        uint8_t *buffer,
        size_t length
    );
//保存上一次状态，用于识别按下和松开
    bool wasTouched_;

    int16_t startX_;
    int16_t startY_;

    int16_t currentX_;
    int16_t currentY_;
};