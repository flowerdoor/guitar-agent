#pragma once

#include <stdint.h>

#include "drivers/touch_driver.h"

class ScorePlayer;
class ScoreRenderer;

//负责拖动跳转
class ScoreScrubber{
    public:
        ScoreScrubber();

        void update(
            const TouchState &touch,
            ScorePlayer &player,
            const ScoreRenderer &renderer
        );

        //当前是否在拖动
        bool isDragging() const;

    private:
        bool isScoreArea(
            int16_t x,
            int16_t y
        )const;
        //开始拖动时记录的播放器设置
        uint32_t dragStartTick_;
        //是否已经进入拖动状态
        bool dragging_;
};