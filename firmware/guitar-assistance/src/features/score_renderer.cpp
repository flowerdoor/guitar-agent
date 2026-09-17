#include "features/score_renderer.h"

#include <Arduino.h>
#include <Adafruit_ILI9341.h>

namespace{
    constexpr int16_t SCREEN_WIDTH = 320;

    constexpr int16_t FIRST_STRING_Y = 58;

    constexpr int16_t STRING_SPACING = 25;

    constexpr int16_t SCORE_START_X = 42;

    constexpr int16_t PIXELS_PER_BEAT = 64;

    constexpr int16_t GRID_TOP = 40;
    constexpr int16_t GRID_BOTTOM = 158;

    constexpr int16_t PLAYHEAD_X = 100;

    const char *STRING_NAMES[ScoreModel::STRING_COUNT] = {
        "e",
        "B",
        "G",
        "D",
        "A",
        "E"
    };
}
//构造函数
ScoreRenderer::ScoreRenderer(DisplayDriver &display)
  : display_(display) {
}
//绘制一整个网格
void ScoreRenderer::render(
    const ScoreModel::TabStep *steps,
    size_t stepCount,
    uint32_t currentTick
){
    if (steps == nullptr || stepCount == 0) {
        display_.clear(ILI9341_BLACK);
        display_.drawText(
            10,
            10,
            "No score data",
            ILI9341_RED,
            2
        );
        return;
    }
    display_.clear(ILI9341_BLACK);

    drawHeader();
    drawBeatGrid(steps,stepCount,currentTick);
    drawPlayhead();
    drawStrings();
    drawNotes(steps,stepCount,currentTick);
}
//绘制标题
void ScoreRenderer::drawHeader() {
    display_.fillRect(
        0,
        0,
        SCREEN_WIDTH,
        32,
        ILI9341_DARKCYAN
    );

    display_.drawText(
        8,
        8,
        "Guitar Assistance",
        ILI9341_WHITE,
        2
    );
}
// 绘制六根弦
void ScoreRenderer::drawStrings(){
    for(size_t stringIndex = 0; stringIndex < ScoreModel::STRING_COUNT;stringIndex++)
    {
        int16_t y = FIRST_STRING_Y + stringIndex * STRING_SPACING;
        display_.drawText(
            4,
            y - 7,
            STRING_NAMES[stringIndex],
            ILI9341_WHITE,
            2
        );
        display_.drawHLine(
            22,
            y,
            SCREEN_WIDTH - 22,
            ILI9341_LIGHTGREY,
            3
        );
    }
}
//映射在x轴上对应时刻的位置
int16_t ScoreRenderer::tickToX(
    uint32_t tick,
    uint32_t currentTick
) const {//tickx坐标可能是反的，后面检查一下
    int64_t tickDelta = static_cast<int64_t>(tick) - static_cast<int64_t>(currentTick);
    return PLAYHEAD_X + tickDelta * PIXELS_PER_BEAT / ScoreModel::TICKS_PER_BEAT;
}

//绘制节拍网格
void ScoreRenderer::drawBeatGrid(
    const ScoreModel:: TabStep *steps,
    size_t stepCount,
    uint32_t currentTick
){
    const ScoreModel::TabStep &lastStep =steps[stepCount - 1];
    uint32_t endTick = lastStep.startTick + lastStep.durationTicks;

    for(uint32_t beatTick = 0; beatTick <= endTick; beatTick += ScoreModel::TICKS_PER_BEAT){
        int16_t x = tickToX(beatTick, currentTick);

        if(x < 22){
            continue;
        }

        if (x >= SCREEN_WIDTH) {
            break;
        }
        int16_t screenX = static_cast<int16_t>(x);

        display_.drawVLine(screenX, GRID_TOP, GRID_BOTTOM - GRID_TOP + 20, ILI9341_LIGHTGREY);

        uint32_t beatNumber = beatTick / ScoreModel::TICKS_PER_BEAT + 1;
        char beatText[8];
        snprintf(beatText,
            sizeof(beatText),
            "%lu",
            static_cast<unsigned long>(beatNumber)
        );
        display_.drawText(
            x + 3,
            38,
            beatText,
            ILI9341_CYAN,
            1
        );
    }
}

//绘制所有品位
void ScoreRenderer::drawNotes(
    const ScoreModel::TabStep *steps,
    size_t stepCount,
    uint32_t currentTick
){
    for (size_t stepIndex = 0;stepIndex < stepCount;stepIndex++) {
        const ScoreModel::TabStep &step = steps[stepIndex];
        int32_t x = tickToX(step.startTick,currentTick);
        if (x < 22) {
            continue;
        }

        if (x >= SCREEN_WIDTH){
            break;
        }

        int16_t screenX = static_cast<int16_t>(x);

        for(size_t stringIndex = 0; stringIndex < ScoreModel::STRING_COUNT;stringIndex++){
            int8_t fret = step.frets[stringIndex];
            if (fret == ScoreModel::NO_NOTE){
                continue;
            }
            int16_t y = FIRST_STRING_Y + static_cast<int16_t>(stringIndex) * STRING_SPACING;
            drawFret(screenX, y, fret);
        }
    }
}
//绘制一个品位
void ScoreRenderer::drawFret(
    int16_t x,
    int16_t y,
    int8_t fret
){
    char fretText[4];

    if(fret == ScoreModel::MUTED){
        snprintf(
            fretText,
            sizeof(fretText),
            "x"
        );
    }
    else{
        snprintf(
            fretText,
            sizeof(fretText),
            "%d",
            fret
        );
    }
    int16_t textWidth = strlen(fretText) * 12;

    display_.fillRect(
        x - textWidth / 2 - 2,
        y - 9,
        textWidth + 4,
        18,
        ILI9341_BLACK
    );
    display_.drawText(
        x - textWidth / 2,
        y - 7,
        fretText,
        ILI9341_YELLOW,
        2
    );
}
//考虑一下，大概率在滚动后需要修改逻辑
int32_t ScoreRenderer::pixelsToTicks(
    int16_t pixels
) const{
    return static_cast<int32_t>(pixels) *
         ScoreModel::TICKS_PER_BEAT /
         PIXELS_PER_BEAT;
}

void ScoreRenderer::drawPlayhead(){
    display_.drawVLine(
        PLAYHEAD_X,
        GRID_TOP,
        145,
        ILI9341_RED
    );
}