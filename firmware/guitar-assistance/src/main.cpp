#include <Arduino.h>
#include "app/application.h"

/*Application application;

void setup() {
  application.begin();
}

void loop() {
  application.update();
}*/

#include <Adafruit_ILI9341.h>

#include "drivers/display_driver.h"
#include "drivers/touch_driver.h"
#include "data/demo_score.h"
#include "features/score_renderer.h"
#include "features/score_player.h"
#include "features/player_ui.h"
#include "features/score_scrubber.h"
#include "features/navigation_ui.h"
// 创建全局显示驱动对象
DisplayDriver display;
TouchDriver touch;
// 初始速度为 72 BPM
ScorePlayer scorePlayer(72);
ScoreRenderer scoreRenderer(display);
ScoreScrubber scoreScrubber;

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("Application starting");

  // 初始化显示屏
  display.begin();
  if (!touch.begin()) {
    Serial.println("Touch initialization failed");
}
  scorePlayer.begin(DemoScore::END_TICK);


  scoreRenderer.render(
    DemoScore::STEPS,
    DemoScore::STEP_COUNT,
    scorePlayer.currentTick(),
    scorePlayer.isPlaying()
  );

  scorePlayer.play();
  
}

void loop() {
    // 先更新计时；到达末尾时 update() 会停止播放
    scorePlayer.update();

    TouchState touchState = touch.read();

    scoreScrubber.update(
        touchState,
        scorePlayer,
        scoreRenderer
    );
    // 只在“松开”那一次处理点击，按住时不会连续触发
      if (touchState.justReleased) {

      Serial.print("Touch released: ");
      Serial.print(touchState.x);
      Serial.print(", ");
      Serial.println(touchState.y);

      Serial.print("Drag delta X: ");
      Serial.println(
          touchState.x - touchState.startX
      );
      PlayerAction pressed = PlayerUi::hitTest(
          touchState.startX,
          touchState.startY
      );

      PlayerAction released = PlayerUi::hitTest(
          touchState.x,
          touchState.y
      );


        // 起点和终点都在按钮内，才视为一次点击
      if (pressed != PlayerAction::None && pressed == released) {
      switch (pressed) {
        case PlayerAction::PreviousBeat:
            scorePlayer.previousBeat();
            break;

        case PlayerAction::TogglePlay:
            scorePlayer.toggle();
            break;

        case PlayerAction::Reset:
            scorePlayer.reset();
            break;

        case PlayerAction::NextBeat:
            scorePlayer.nextBeat();
            break;

        case PlayerAction::None:
            break;
      }
    }
    NavigationAction topPressed =
    NavigationUi::hitTest(
        touchState.startX,
        touchState.startY
    );

NavigationAction topReleased =
    NavigationUi::hitTest(
        touchState.x,
        touchState.y
    );

if (topPressed != NavigationAction::None &&
    topPressed == topReleased) {
    switch (topPressed) {
        case NavigationAction::OpenScoreMenu:
            Serial.println("Open score menu");
            break;

        case NavigationAction::GoBack:
            Serial.println("Go back");
            break;

        case NavigationAction::None:
            break;
    }
}
  }
  static uint32_t lastRenderTime = 0;

  if (millis() - lastRenderTime >= 30) {
        lastRenderTime = millis();

        scoreRenderer.render(
            DemoScore::STEPS,
            DemoScore::STEP_COUNT,
            scorePlayer.currentTick(),
            scorePlayer.isPlaying()
        );
    }
}