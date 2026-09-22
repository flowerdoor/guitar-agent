#include "features/navigation_ui.h"

#include "drivers/display_driver.h"

#include <Adafruit_ILI9341.h>

namespace{
    constexpr int16_t BUTTON_WIDTH = 32;
    constexpr int16_t TOP_HEIGHT = 40;

    void drawMenuIcon(DisplayDriver &display){
        display.fillRect(13, 8, 20, 4, ILI9341_WHITE);
        display.fillRect(13, 16, 20, 4, ILI9341_WHITE);
        display.fillRect(13, 24, 20, 4, ILI9341_WHITE);
    }

    void drawBackIcon(DisplayDriver &display){
        display.fillRect(294, 17, 15, 3, ILI9341_WHITE);

        display.fillTriangle(
            286, 18,
            300, 7,
            300, 27,
            ILI9341_WHITE
        );
    }
}
//绘制顶部栏
void NavigationUi::drawTopBar(DisplayDriver &display){
    display.fillRect(
        0,
        0,
        319,
        TOP_HEIGHT-7,
        ILI9341_DARKCYAN
    );

    drawMenuIcon(display);
    drawBackIcon(display);

}

NavigationAction NavigationUi::hitTest(int16_t x, int16_t y){
    if (y < 0 || y >= TOP_HEIGHT) {
        return NavigationAction::None;
    }
    
    if(x >= 0 && x < BUTTON_WIDTH && y >= 0 && y < TOP_HEIGHT){
        return NavigationAction::OpenScoreMenu;
    }

    if(x >= 280 && x < 320 && y >= 0 && y < TOP_HEIGHT){
        return NavigationAction::GoBack;
    }

    return NavigationAction::None;
}

