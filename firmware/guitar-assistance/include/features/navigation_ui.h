#pragma once

#include<stdint.h>

class DisplayDriver;

enum class NavigationAction{
    None,
    OpenScoreMenu,
    GoBack
};

class NavigationUi{
public:
    static void drawTopBar(DisplayDriver &display);

    static NavigationAction hitTest(int16_t x, int16_t y);
};
