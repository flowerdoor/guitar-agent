#pragma once

#include<stdint.h>

class DisplayDriver;

enum class PlayerAction{
    None,
    PreviousBeat,
    TogglePlay,
    Reset,
    NextBeat
};

//负责播放器页面的按钮外观和区域判断
class PlayerUi{
public:
    static void drawControls(DisplayDriver &display, bool playing);

    static PlayerAction hitTest(int16_t x, int16_t y);

    static bool isScoreAreaHit(
        int16_t x,
        int16_t y
    );
};