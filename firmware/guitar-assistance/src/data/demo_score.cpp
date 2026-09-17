#include "data/demo_score.h"



namespace DemoScore {

    using ScoreModel::MUTED;
    using ScoreModel::NO_NOTE;
    using ScoreModel::TabStep;
    const TabStep STEPS[] = {
  /*
   * 第 1 小节，第 1 拍前半拍
   *
   * C 和弦：
   * e|--0--
   * B|--1--
   * G|--0--
   * D|--2--
   * A|--3--
   * E|-----
   */
  {
    0,                              // 开始 Tick
    240,                            // 持续半拍
    {0, 1, 0, 2, 3, NO_NOTE},       // 六根弦
    1,                              // 第 1 小节
    1                               // 第 1 拍
  },

  // 第 1 拍后半拍：A 弦 3 品
  {
    240,
    240,
    {NO_NOTE, NO_NOTE, NO_NOTE, NO_NOTE, 3, NO_NOTE},
    1,
    1
  },

  // 第 2 拍前半拍：D 弦 2 品
  {
    480,
    240,
    {NO_NOTE, NO_NOTE, NO_NOTE, 2, NO_NOTE, NO_NOTE},
    1,
    2
  },

  // 第 2 拍后半拍：G 弦空弦
  {
    720,
    240,
    {NO_NOTE, NO_NOTE, 0, NO_NOTE, NO_NOTE, NO_NOTE},
    1,
    2
  },

  // 第 3 拍前半拍：B 弦 1 品
  {
    960,
    240,
    {NO_NOTE, 1, NO_NOTE, NO_NOTE, NO_NOTE, NO_NOTE},
    1,
    3
  },

  // 第 3 拍后半拍：高音 e 空弦
  {
    1200,
    240,
    {0, NO_NOTE, NO_NOTE, NO_NOTE, NO_NOTE, NO_NOTE},
    1,
    3
  },

  // 第 4 拍前半拍：闷音
  {
    1440,
    240,
    {MUTED, MUTED, MUTED, MUTED, MUTED, MUTED},
    1,
    4
  },

  // 第 4 拍后半拍：G 和弦
  {
    1680,
    240,
    {3, 0, 0, 0, 2, 3},
    1,
    4
  }
};
    const size_t STEP_COUNT = sizeof(STEPS) / sizeof(STEPS[0]);
    const uint32_t END_TICK =STEPS[STEP_COUNT - 1].startTick + STEPS[STEP_COUNT - 1].durationTicks;
}