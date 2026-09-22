#include "drivers/display_driver.h"

#include <Arduino.h>
#include <SPI.h>

#include "config/board_pins.h"

DisplayDriver::DisplayDriver()
    : lcd_(
        BoardPins::LCD_CS, 
        BoardPins::LCD_DC, 
        BoardPins::LCD_RST
    ) ,frame_(
      BoardPins::SCREEN_WIDTH,
      BoardPins::SCREEN_HEIGHT
    ){
}

// 初始化显示屏
void DisplayDriver::begin() {
    pinMode(BoardPins::LCD_BL, OUTPUT);
    digitalWrite(BoardPins::LCD_BL, LOW); // 关闭背光
    //初始化spi
    SPI.begin(
        BoardPins::LCD_SCK,
        BoardPins::LCD_MISO,
        BoardPins::LCD_MOSI,
        BoardPins::LCD_CS
    );

    //初始化ILi9341
    lcd_.begin(BoardPins::LCD_SPI_FREQUENCY);

    lcd_.setRotation(1); // 横屏显示，分辨率为 320 x 240

    if(frame_.getBuffer() == nullptr){
        Serial.println("ERROR: Failed to allocate frame buffer");
        while(1){
          delay(1000);
        }
    }

    frame_.fillScreen(ILI9341_BLACK); // 清屏
    present();

    digitalWrite(BoardPins::LCD_BL, HIGH);
}

// 清屏
void DisplayDriver::clear(uint16_t color) {
    frame_.fillScreen(color);
}

void DisplayDriver::drawText(
  int16_t x,
  int16_t y,
  const char *text,
  uint16_t color,
  uint8_t size
) {
  frame_.setCursor(x, y);
  frame_.setTextSize(size);
  frame_.setTextColor(color,ILI9341_BLACK);
  frame_.setTextWrap(false);
  frame_.print(text);
}

void DisplayDriver::drawHLine(
  int16_t x,
  int16_t y,
  int16_t width,
  uint16_t color,
  int16_t thickness
) {
  if (width <= 0 || thickness <= 0) {
    return;
  }
  frame_.fillRect(
    x,
    y - thickness /2,
    width,
    thickness,
    color
  );
}

void DisplayDriver::drawVLine(
  int16_t x,
  int16_t y,
  int16_t height,
  uint16_t color
) {
  frame_.drawFastVLine(
    x,
    y,
    height,
    color
  );
}
//填充矩形。
void DisplayDriver::fillRect(
  int16_t x,
  int16_t y,
  int16_t width,
  int16_t height,
  uint16_t color
) {
  frame_.fillRect(
    x,
    y,
    width,
    height,
    color
  );
}

void DisplayDriver::fillTriangle(
    int16_t x0, int16_t y0,
    int16_t x1, int16_t y1,
    int16_t x2, int16_t y2,
    uint16_t color
) {
    frame_.fillTriangle(x0, y0, x1, y1, x2, y2, color);
}

void DisplayDriver::drawCircle(
  int16_t x,
  int16_t y,
  int16_t radius,
  uint16_t color
){
  frame_.drawCircle(x,y,radius,color);
}

void DisplayDriver::present(){
  lcd_.drawRGBBitmap(
    0,
    0,
    frame_.getBuffer(),
    BoardPins::SCREEN_WIDTH,
    BoardPins::SCREEN_HEIGHT
  );
}