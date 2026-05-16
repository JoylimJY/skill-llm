/**
 * State Machine - 状态机模式实现
 * 
 * 管理第一性原理分析过程的状态流转
 * 灵感来源：meta-skill-weaver 状态持久化系统
 * 
 * 设计模式：状态模式 (State Pattern)
 * - 封装状态相关的行为
 * - 状态变更时自动触发转换逻辑
 * - 防止非法状态转换
 */

// ============================================================
// 状态定义
// ============================================================

/**
 * 分析状态枚举
 */
const ANALYSIS_STATUS = {
  IDLE: 'idle',                      // 空闲状态，等待新分析
  ANALYZING: 'analyzing',            // 分析进行中
  PAUSED: 'paused',                  // 分析已暂停
  WAITING_INPUT: 'waiting_input',    // 等待用户输入
  COMPLETED: 'completed',            // 分析完成，报告已生成
  FAILED: 'failed'                   // 分析失败
};

/**
 * 状态转换规则
 */
const STATE_TRANSITIONS = {
  [ANALYSIS_STATUS.IDLE]: [ANALYSIS_STATUS.ANALYZING, ANALYSIS_STATUS.FAILED],
  [ANALYSIS_STATUS.ANALYZING]: [ANALYSIS_STATUS.PAUSED, ANALYSIS_STATUS.WAITING_INPUT, ANALYSIS_STATUS.COMPLETED, ANALYSIS_STATUS.FAILED],
  [ANALYSIS_STATUS.PAUSED]: [ANALYSIS_STATUS.ANALYZING, ANALYSIS_STATUS.FAILED],
  [ANALYSIS_STATUS.WAITING_INPUT]: [ANALYSIS_STATUS.ANALYZING, ANALYSIS_STATUS.COMPLETED, ANALYSIS_STATUS.FAILED],
  [ANALYSIS_STATUS.COMPLETED]: [ANALYSIS_STATUS.IDLE],
  [ANALYSIS_STATUS.FAILED]: [ANALYSIS_STATUS.IDLE]
};

/**
 * 状态元数据
 */
const STATE_METADATA = {
  [ANALYSIS_STATUS.IDLE]: { label: '空闲', description: '等待新的分析任务', canResume: false, canExport: false },
  [ANALYSIS_STATUS.ANALYZING]: { label: '分析中', description: '正在进行第一性原理分析', canResume: false, canExport: false },
  [ANALYSIS_STATUS.PAUSED]: { label: '已暂停', description: '分析已暂停，可以恢复', canResume: true, canExport: true },
  [ANALYSIS_STATUS.WAITING_INPUT]: { label: '等待输入', description: '等待用户提供更多信息', canResume: true, canExport: false },
  [ANALYSIS_STATUS.COMPLETED]: { label: '已完成', description: '分析完成，报告已生成', canResume: false, canExport: true },
  [ANALYSIS_STATUS.FAILED]: { label: '已失败', description: '分析过程中发生错误', canResume: false, canExport: false }
};

// ============================================================
// 状态机类
// ============================================================

class AnalysisStateMachine {
  constructor(analysisId, options = {}) {
    this.analysisId = analysisId;
    this.currentState = ANALYSIS_STATUS.IDLE;
    this.stateHistory = [];
    this.metadata = {
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      ...options
    };
    this._recordStateTransition(null, ANALYSIS_STATUS.IDLE, '初始化');
  }
  
  _recordStateTransition(fromState, toState, reason = '') {
    this.stateHistory.push({ fromState, toState, reason, timestamp: new Date().toISOString() });
    this.metadata.updatedAt = new Date().toISOString();
  }
  
  _canTransition(toState) {
    const allowedTransitions = STATE_TRANSITIONS[this.currentState];
    if (!allowedTransitions) return false;
    return allowedTransitions.includes(toState);
  }
  
  transition(toState, reason = '') {
    if (!Object.values(ANALYSIS_STATUS).includes(toState)) return false;
    if (this.currentState === toState) return true;
    if (!this._canTransition(toState)) return false;
    
    const fromState = this.currentState;
    this.currentState = toState;
    this._recordStateTransition(fromState, toState, reason);
    return true;
  }
  
  getState() { return this.currentState; }
  getStateMetadata() { return STATE_METADATA[this.currentState] || {}; }
  canResume() { return this.getStateMetadata().canResume || false; }
  canExport() { return this.getStateMetadata().canExport || false; }
  getStateHistory() { return [...this.stateHistory]; }
  
  getSnapshot() {
    return {
      analysisId: this.analysisId,
      currentState: this.currentState,
      stateHistory: this.stateHistory,
      metadata: this.metadata
    };
  }
  
  static fromSnapshot(snapshot) {
    const machine = new AnalysisStateMachine(snapshot.analysisId, snapshot.metadata);
    machine.currentState = snapshot.currentState;
    machine.stateHistory = snapshot.stateHistory || [];
    return machine;
  }
  
  reset() { this.transition(ANALYSIS_STATUS.IDLE, '重置'); }
}

// ============================================================
// 状态机管理器
// ============================================================

class StateMachineManager {
  constructor() { this.machines = new Map(); }
  
  getOrCreate(analysisId, options = {}) {
    if (!this.machines.has(analysisId)) {
      this.machines.set(analysisId, new AnalysisStateMachine(analysisId, options));
    }
    return this.machines.get(analysisId);
  }
  
  get(analysisId) { return this.machines.get(analysisId) || null; }
  delete(analysisId) { this.machines.delete(analysisId); }
  getAllSnapshots() { return Array.from(this.machines.values()).map(m => m.getSnapshot()); }
  
  getActiveAnalysisIds() {
    return Array.from(this.machines.entries())
      .filter(([_, m]) => [ANALYSIS_STATUS.ANALYZING, ANALYSIS_STATUS.PAUSED, ANALYSIS_STATUS.WAITING_INPUT].includes(m.getState()))
      .map(([id]) => id);
  }
}

module.exports = { ANALYSIS_STATUS, STATE_TRANSITIONS, STATE_METADATA, AnalysisStateMachine, StateMachineManager };
