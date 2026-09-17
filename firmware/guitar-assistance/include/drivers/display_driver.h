#pragma once

#include <stdint.h>
#include <Adafruit_ILI9341.h>
#include <Adafruit_GFX.h>

class DisplayDriver {
public:
//创建驱动对象
    DisplayDriver();

    void begin();
    void clear(uint16_t color);
    void drawText(
        int16_t x,
        int16_t y,
        const char *text,
        uint16_t color,
        uint8_t size
    );
    void drawHLine(
        int16_t x,
        int16_t y,
        int16_t width,
        uint16_t color,
        int16_t thickness

    );
    // 绘制垂直线，用于表示节拍和小节
    void drawVLine(
    int16_t x,
    int16_t y,
    int16_t height,
    uint16_t color
    );
    void fillRect(
        int16_t x,
        int16_t y,
        int16_t width,
        int16_t height,
        uint16_t color
    );
    private:
    Adafruit_ILI9341 lcd_;
};