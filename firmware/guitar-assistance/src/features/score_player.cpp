#include "features/score_player.h"

#include <Arduino.h>

#include "models/tab_step.h"

//构造函数
ScorePlayer::ScorePlayer(uint16_t bpm)
    : bpm_(bpm),
      totalTicks_(0),
      anchorTick_(0),
      anchorTimeMs_(0),
      pausedTick_(0),
      playing_(false) {
}

//初始化
void ScorePlayer::begin(uint32_t totalTicks) {
    totalTicks_ = totalTicks;

    anchorTick_ = 0;
    anchorTimeMs_ = millis();
    pausedTick_ = 0;
    playing_ = false;
}
//更新播放器
void ScorePlayer::update(){
    if(!playing_){
        return;
    }
    //到达乐谱末尾后自动暂停
    if(currentTick() >= totalTicks_){
        playing_ = false;
        pausedTick_ = totalTicks_;
    }   
}

//计算当前tick
uint32_t ScorePlayer::currentTick() const {
    if(!playing_){
        return pausedTick_;
    }
    uint32_t elapsedMs = millis() - anchorTimeMs_;

    uint32_t elapsedTicks = static_cast<uint64_t>(elapsedMs) * bpm_ *ScoreModel::TICKS_PER_BEAT / 60000ULL;

    uint32_t tick = anchorTick_ + static_cast<uint32_t>(elapsedTicks);
    return clampTick(tick);
}
//播放控制部分
//开始或继续播放
void ScorePlayer::play(){
    if(playing_){
        return;
    }

    if (pausedTick_ >= totalTicks_){
        pausedTick_ = 0;
    }

    anchorTick_ = pausedTick_;
    anchorTimeMs_ = millis();
    playing_ =true;
}

//暂停
void ScorePlayer::pause(){
    if(!playing_){
        return;
    }
    pausedTick_ = currentTick();
    playing_ = false;
}

//在暂停和播放间切换
void ScorePlayer::toggle(){
    if(playing_){
        pause();
    }else{
        play();
    }
}
//重置
void ScorePlayer::reset(){
    pausedTick_ = 0;
    anchorTick_ = 0;
    anchorTimeMs_ = millis();
    playing_ = false;
}

//跳转控制
void ScorePlayer::seek(uint32_t tick){
    tick = clampTick(tick);

    pausedTick_ = tick;
    anchorTick_ = tick;
    anchorTimeMs_ = millis();
    // 到达末尾后停止播放
    playing_ = false;
}

//上一拍
void ScorePlayer::previousBeat(){
    uint32_t tick =currentTick();
//找到当前拍的起始位置
    uint32_t currentBeatStart = tick / ScoreModel::TICKS_PER_BEAT * ScoreModel::TICKS_PER_BEAT;
    if (currentBeatStart >= ScoreModel::TICKS_PER_BEAT) {
        seek(currentBeatStart - ScoreModel::TICKS_PER_BEAT);
    }
    else{
        seek(0);
    }
}

void ScorePlayer::nextBeat(){
    uint32_t tick = currentTick();
    uint32_t nextBeatStart = (tick / ScoreModel::TICKS_PER_BEAT + 1) * ScoreModel::TICKS_PER_BEAT;
    seek(nextBeatStart);
}

// bpm控制
void ScorePlayer::setBpm(uint16_t bpm){
    if(bpm == 0){
        return;
    }

    uint32_t tick = currentTick();

    bpm_ = bpm;
    pausedTick_ = tick;
    anchorTick_ = tick;
    anchorTimeMs_ = millis();
}

uint16_t ScorePlayer::bpm() const{
    return bpm_;
}

//状态查询
bool ScorePlayer::isPlaying() const{
    return playing_;
}

bool ScorePlayer::isFinished() const{
    return !playing_ && currentTick() >= totalTicks_;
}
//边界保护
uint32_t ScorePlayer::clampTick(uint32_t tick)const{
    if (tick > totalTicks_) {
        return totalTicks_;
    }

    return tick;
}
// 获取乐谱总 Tick 数
uint32_t ScorePlayer::totalTicks() const {
    return totalTicks_;
}
