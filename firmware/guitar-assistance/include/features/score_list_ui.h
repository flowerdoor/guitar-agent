#pragma once
#include <stdint.h>

#include "drivers\display_driver.h"

class DisplayDriver;

class ScoreListUi{
public:
    //绘制乐谱列表页面
    static void draw(DisplayDriver &display);

    //检查点击位置是否在乐谱列表区域内
    static bool isScoreListArea(int16_t x, int16_t y);
};