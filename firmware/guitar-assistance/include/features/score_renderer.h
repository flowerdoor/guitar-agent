#pragma once

#include <stddef.h>
#include <stdint.h>

#include "drivers/display_driver.h"
#include "models/tab_step.h"

class ScoreRenderer {
public:
    explicit ScoreRenderer(DisplayDriver &display);
      /*
   * 绘制一段完整的静态乐谱。
   *
   * steps     乐谱数组
   * stepCount 数组中有多少个时间格
   */
    void render(
        const ScoreModel::TabStep *steps,
        size_t stepCount,
        uint32_t currentTick
    );
    // 将屏幕横坐标转换为 Tick
    int32_t pixelsToTicks(int16_t pixels) const;
private:
    // 绘制标题
    void drawHeader();

    // 绘制六根弦
    void drawStrings();

    // 绘制节拍分隔线和拍号
    void drawBeatGrid(
        const ScoreModel::TabStep *steps,
        size_t stepCount,
        uint32_t currentTick
    );
        // 绘制所有品位数字
    void drawNotes(
        const ScoreModel::TabStep *steps,
        size_t stepCount,
        uint32_t currentTick
    ); 
    //绘制演奏头
    void drawPlayhead();
    // 绘制一个品位数字或闷音符号
    void drawFret(
        int16_t x,
        int16_t y,
        int8_t fret
    );
    // 将 Tick 转换为屏幕横坐标
    int16_t tickToX(
        uint32_t tick,
        uint32_t currentTick
    ) const;
    // 保存传入的显示驱动引用
    DisplayDriver &display_;
};