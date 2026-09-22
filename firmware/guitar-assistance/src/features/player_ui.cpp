#include "features/player_ui.h"

#include <Adafruit_ILI9341.h>

#include "drivers/display_driver.h"

namespace{
    // 播放/暂停按钮的区域
    constexpr int16_t BAR_Y = 194;
    constexpr int16_t BAR_HEIGHT = 46;
    constexpr int16_t BUTTON_WIDTH = 80;
    constexpr int16_t ICON_Y = 217;

    void drawBackground(
        DisplayDriver &display,
        int16_t index,
        uint16_t color
    ){
        display.fillRect(
            index*BUTTON_WIDTH +1,
            BAR_Y,
            BUTTON_WIDTH - 2,
            BAR_HEIGHT,
            color
        );
    }
}

void PlayerUi::drawControls(DisplayDriver &display, bool playing){
    const uint16_t normal = ILI9341_DARKCYAN;
    const uint16_t active = ILI9341_DARKGREEN;
    const uint16_t icon = ILI9341_WHITE;

    drawBackground(display,0,normal);
    drawBackground(display,1,playing ? normal : active);
    drawBackground(display,2,normal);
    drawBackground(display,3,normal);

    display.fillRect(25, ICON_Y - 12, 3, 24, icon);
    display.fillTriangle(
        29, ICON_Y,
        51, ICON_Y - 12,
        51, ICON_Y + 12,
        icon
    );

    if (playing) {
        display.fillRect(109, ICON_Y - 11, 7, 22, icon);
        display.fillRect(124, ICON_Y - 11, 7, 22, icon);
    } else {
        display.fillTriangle(
            111, ICON_Y - 12,
            111, ICON_Y + 12,
            132, ICON_Y,
            icon
        );
    }

    display.drawCircle(200, ICON_Y, 12, icon);
    display.drawCircle(200, ICON_Y, 11, icon);

    // 用按钮背景色擦掉左上方的一小段圆弧
    display.fillRect(185, ICON_Y - 15, 12, 9, normal);
    display.fillTriangle(
        187, ICON_Y - 8,
        200, ICON_Y - 12,
        196, ICON_Y,
        icon
    );

    // 下一拍：向右三角形 + 竖线，中心 x=280
    display.fillTriangle(
        269, ICON_Y - 12,
        269, ICON_Y + 12,
        291, ICON_Y,
        icon
    );
    display.fillRect(292, ICON_Y - 12, 3, 24, icon);
}

PlayerAction PlayerUi::hitTest(int16_t x, int16_t y){
    if(x < 0 || x >= 320 || y<BAR_Y || y >= BAR_Y + BAR_HEIGHT){
            return PlayerAction::None;
    }

    switch (x / BUTTON_WIDTH) {
        case 0: return PlayerAction::PreviousBeat;
        case 1: return PlayerAction::TogglePlay;
        case 2: return PlayerAction::Reset;
        case 3: return PlayerAction::NextBeat;
        default: return PlayerAction::None;
    }
}
