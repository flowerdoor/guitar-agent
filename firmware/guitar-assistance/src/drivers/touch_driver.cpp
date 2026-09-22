#include "drivers/touch_driver.h"

#include <Arduino.h>
#include <Wire.h>

#include "config/board_pins.h"

namespace{
    constexpr uint8_t FT6336_ADDRESS = 0x38;

    constexpr uint8_t REG_TOUCH_COUNT = 0x02;
    constexpr uint8_t REG_POINT1_XH = 0x03;
    constexpr uint8_t REG_CHIP_ID = 0xA3;
}

TouchDriver::TouchDriver()
    : wasTouched_(false),
      startX_(0),
      startY_(0),
      currentX_(0),
      currentY_(0) {
}

bool TouchDriver::begin(){
    pinMode(BoardPins::TOUCH_INT,INPUT_PULLUP);
    pinMode(BoardPins::TOUCH_RST,OUTPUT);
//复位触摸控制器
    digitalWrite(BoardPins::TOUCH_RST,LOW);
    delay(10);
    digitalWrite(BoardPins::TOUCH_RST,HIGH);
    delay(200);

    Wire.begin(
        BoardPins::TOUCH_SDA,
        BoardPins::TOUCH_SCL
    );

    Wire.setClock(400000);

    uint8_t chipId = 0;
    if(!readRegister(REG_CHIP_ID,chipId)){
        Serial.println("ERROR: FT6336U not found");
        return false;
    }

    Serial.print("FT6336U found, chip ID: 0x");
    Serial.println(chipId,HEX);

    return true;
}

TouchState TouchDriver::read(){
    TouchState state = {
        wasTouched_,
        false,
        false,
        currentX_,
        currentY_,
        startX_,
        startY_
    };

    uint8_t touchCount = 0;

    //通信失败时保持原状态，避免产生错误的松开事件
    if(!readRegister(REG_TOUCH_COUNT,touchCount)){
        return state;
    }

    bool touched = (touchCount &0x0F) > 0;

    if(touched){
        uint8_t pointData[4];
        if(!readRegisters(
            REG_POINT1_XH,
            pointData,
            sizeof(pointData)
        )){
            return state;
        }

        int16_t rawX = ((pointData[0] & 0x0F) << 8) | pointData[1];
        int16_t rawY = ((pointData[2] & 0x0F) << 8) | pointData[3];

        // 触摸原始坐标是竖屏方向；显示屏当前是横屏 setRotation(1)
        currentX_ = rawY;
        currentY_ = BoardPins::SCREEN_HEIGHT - 1 - rawX; // 239 - rawX
        
        currentX_ = constrain(currentX_,0,BoardPins::SCREEN_WIDTH - 1);
        currentY_ = constrain(currentY_,0,BoardPins::SCREEN_HEIGHT - 1);

        if(!wasTouched_){
            startX_ = currentX_;
            startY_ = currentY_;
        }
    }

    state.touched = touched;
    state.justPressed = touched && !wasTouched_;
    state.justReleased = !touched && wasTouched_;

    state.x = currentX_;
    state.y = currentY_;
    state.startX = startX_;
    state.startY = startY_;

    wasTouched_ = touched;
    return state;
}

bool TouchDriver::readRegister(
    uint8_t reg,
    uint8_t &value
){
    return readRegisters(reg,&value,1);
}

bool TouchDriver::readRegisters(
    uint8_t reg,
    uint8_t *buffer,
    size_t length
){
    Wire.beginTransmission(FT6336_ADDRESS);
    Wire.write(reg);

    if(Wire.endTransmission(false) != 0){
        return false;
    }

    size_t received = Wire.requestFrom(
        FT6336_ADDRESS,
        static_cast<uint8_t>(length)
    );

    if(received != length){
        return false;
    }

    for(size_t index = 0;index < length;index++){
        buffer[index] = Wire.read();
    }

    return true;
}