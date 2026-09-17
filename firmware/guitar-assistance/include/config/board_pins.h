#pragma once

#include <stdint.h>

namespace BoardPins {
    //SPI时钟
    constexpr int8_t LCD_SCK  = 12;
    //SPI数据输出
    constexpr int8_t LCD_MOSI = 11;
    //屏幕片选
    constexpr int8_t LCD_CS   = 10;
    //屏幕数据/命令选择
    constexpr int8_t LCD_DC   = 9;
    //复位
    constexpr int8_t LCD_RST  = 8;
    //背光控制
    constexpr int8_t LCD_BL   = 14;
    // 当前不读取屏幕，因此不使用 MISO
    constexpr int8_t LCD_MISO = -1;

    /*电容屏*/
    // I2C 数据
    constexpr int8_t TOUCH_SDA = 4;

    // I2C 时钟
    constexpr int8_t TOUCH_SCL = 5;

    // 触摸中断
    constexpr int8_t TOUCH_INT = 6;

    // 触摸复位
    constexpr int8_t TOUCH_RST = 7;
    /*屏幕参数*/
    constexpr int16_t SCREEN_WIDTH  = 320;
    constexpr int16_t SCREEN_HEIGHT = 240;

    constexpr uint32_t LCD_SPI_FREQUENCY = 20000000; // 20 MHz
}