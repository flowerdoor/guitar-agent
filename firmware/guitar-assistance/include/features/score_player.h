#pragma once

#include <stdint.h>
//负责播放暂停跳转，记录时间信息
class ScorePlayer {
public:
//创建播放器
    explicit ScorePlayer(uint16_t bpm);
//设置乐谱总长
    void begin(uint32_t totalTicks);
//用于检查是否播放结束
    void update();
    //开始或继续播放
    void play();
    //暂停播放
    void pause();
    //在暂停和播放间切换
    void toggle();
    //回到乐谱开头并暂停
    void reset();
    //跳转到指定 Tick 并暂停
    void seek(uint32_t tick);
    //跳到上一拍
    void previousBeat();
    //跳到下一拍
    void nextBeat();
    //修改bpm
    void setBpm(uint16_t bpm);
    //获取bpm
    uint16_t bpm() const;
    //获取当前播放位置
    uint32_t currentTick() const;
    //是否正在播放
    bool isPlaying() const;
    //是否已经播放完成
    bool isFinished() const;
    // 获取乐谱总 Tick 数
    uint32_t totalTicks() const;    
private:
    uint32_t clampTick(uint32_t tick) const;

    uint16_t bpm_;
    uint32_t totalTicks_;

    //播放锚点
    uint32_t anchorTick_;
    uint32_t anchorTimeMs_;

    uint32_t pausedTick_;

    bool playing_;
};