#include "features/score_scrubber.h"
#include "features/score_player.h"
#include "features/score_renderer.h"

namespace{
    constexpr int16_t SCORE_LEFT = 22;
    constexpr int16_t SCORE_TOP = 32;
    constexpr int16_t SCORE_BUTTON = 194;
    constexpr int16_t SCORE_RIGHT = 319;
}

ScoreScrubber::ScoreScrubber()
    : dragStartTick_(0),
      dragging_(false) {
}

bool ScoreScrubber::isScoreArea(int16_t x, int16_t y) const {
    return x >= SCORE_LEFT && x <= SCORE_RIGHT &&
           y >= SCORE_TOP && y < SCORE_BUTTON;
}

void ScoreScrubber::update(
    const TouchState &touch,
    ScorePlayer &player,
    const ScoreRenderer &renderer
){
    if(touch.justPressed){
        if(isScoreArea(touch.x, touch.y)){
            // 在播放中按下乐谱区域时，先保存当前位置再暂停。
            // 这样拖动的起点不会因为暂停动作而丢失。
            if(player.isPlaying()){
                player.pause();
            }

            dragging_ = true;
            dragStartTick_ = player.currentTick();
        }
    }

    if(touch.touched&&dragging_){
        int16_t deltaX = touch.x -touch.startX;
        int32_t deltaTicks = renderer.pixelsToTicks(deltaX);

        int64_t targetTick = static_cast<int64_t>(dragStartTick_) - static_cast<int64_t>(deltaTicks);
        if(targetTick < 0){
            targetTick = 0;
        }

        if(targetTick > static_cast<int64_t>(player.totalTicks())){
            targetTick = player.totalTicks();
        }
        player.seek(static_cast<uint32_t>(targetTick));
    }

    if (touch.justReleased){
        dragging_ = false;
    }
}

bool ScoreScrubber::isDragging() const {
    return dragging_;
}
