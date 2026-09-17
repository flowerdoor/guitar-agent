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
#include "data/demo_score.h"
#include "features/score_renderer.h"
#include "features/score_player.h"
// 创建全局显示驱动对象
DisplayDriver display;
// 初始速度为 72 BPM
ScorePlayer scorePlayer(72);
ScoreRenderer scoreRenderer(display);
void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("Application starting");

  // 初始化显示屏
  display.begin();
  scorePlayer.begin(DemoScore::END_TICK);


  scoreRenderer.render(
    DemoScore::STEPS,
    DemoScore::STEP_COUNT,
    scorePlayer.currentTick()
  );

  scorePlayer.play();
  
}

void loop() {
  scorePlayer.update();
  static uint32_t lastRenderTime = 0;
  if(millis() - lastRenderTime >= 50 ){
    lastRenderTime = millis();

    scoreRenderer.render(
      DemoScore::STEPS,
      DemoScore::STEP_COUNT,
      scorePlayer.currentTick()
    );
  }
}