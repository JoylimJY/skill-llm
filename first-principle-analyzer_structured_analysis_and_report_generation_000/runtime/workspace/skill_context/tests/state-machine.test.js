/**
 * State Machine 测试
 */

const {
  ANALYSIS_STATUS,
  AnalysisStateMachine,
  StateMachineManager
} = require('../src/state-machine');

describe('AnalysisStateMachine', () => {
  let machine;
  
  beforeEach(() => {
    machine = new AnalysisStateMachine('test-001');
  });
  
  describe('初始化', () => {
    test('应该初始化为 IDLE 状态', () => {
      expect(machine.getState()).toBe(ANALYSIS_STATUS.IDLE);
    });
    
    test('应该记录初始状态历史', () => {
      const history = machine.getStateHistory();
      expect(history.length).toBe(1);
      expect(history[0].reason).toBe('初始化');
      expect(history[0].toState).toBe(ANALYSIS_STATUS.IDLE);
    });
  });
  
  describe('状态转换', () => {
    test('应该允许从 IDLE 转换到 ANALYZING', () => {
      const result = machine.transition(ANALYSIS_STATUS.ANALYZING, '开始分析');
      expect(result).toBe(true);
      expect(machine.getState()).toBe(ANALYSIS_STATUS.ANALYZING);
    });
    
    test('应该拒绝非法状态转换', () => {
      const result = machine.transition(ANALYSIS_STATUS.COMPLETED, '直接完成');
      expect(result).toBe(false);
      expect(machine.getState()).toBe(ANALYSIS_STATUS.IDLE);
    });
    
    test('应该记录状态转换历史', () => {
      machine.transition(ANALYSIS_STATUS.ANALYZING, '开始分析');
      machine.transition(ANALYSIS_STATUS.PAUSED, '用户暂停');
      
      const history = machine.getStateHistory();
      expect(history.length).toBe(3);
      expect(history[1].toState).toBe(ANALYSIS_STATUS.ANALYZING);
      expect(history[2].toState).toBe(ANALYSIS_STATUS.PAUSED);
    });
    
    test('相同状态转换应该返回 true 但不记录', () => {
      machine.transition(ANALYSIS_STATUS.ANALYZING, '开始');
      const initialHistoryLength = machine.getStateHistory().length;
      
      machine.transition(ANALYSIS_STATUS.ANALYZING, '重复');
      expect(machine.getStateHistory().length).toBe(initialHistoryLength);
    });
  });
  
  describe('状态元数据', () => {
    test('应该返回正确的状态元数据', () => {
      const metadata = machine.getStateMetadata();
      expect(metadata.label).toBe('空闲');
      expect(metadata.canResume).toBe(false);
      expect(metadata.canExport).toBe(false);
    });
    
    test('PAUSED 状态应该可以恢复', () => {
      machine.transition(ANALYSIS_STATUS.ANALYZING);
      machine.transition(ANALYSIS_STATUS.PAUSED);
      
      expect(machine.canResume()).toBe(true);
      expect(machine.canExport()).toBe(true);
    });
    
    test('COMPLETED 状态应该可以导出', () => {
      machine.transition(ANALYSIS_STATUS.ANALYZING);
      machine.transition(ANALYSIS_STATUS.COMPLETED);
      
      expect(machine.canExport()).toBe(true);
      expect(machine.canResume()).toBe(false);
    });
  });
  
  describe('快照与恢复', () => {
    test('应该能够获取快照', () => {
      machine.transition(ANALYSIS_STATUS.ANALYZING, '开始');
      const snapshot = machine.getSnapshot();
      
      expect(snapshot.analysisId).toBe('test-001');
      expect(snapshot.currentState).toBe(ANALYSIS_STATUS.ANALYZING);
      expect(snapshot.stateHistory).toBeDefined();
    });
    
    test('应该能够从快照恢复', () => {
      machine.transition(ANALYSIS_STATUS.ANALYZING, '开始');
      machine.transition(ANALYSIS_STATUS.PAUSED, '暂停');
      
      const snapshot = machine.getSnapshot();
      const restored = AnalysisStateMachine.fromSnapshot(snapshot);
      
      expect(restored.getState()).toBe(ANALYSIS_STATUS.PAUSED);
      expect(restored.analysisId).toBe('test-001');
    });
  });
  
  describe('重置', () => {
    test('应该能够重置到 IDLE 状态', () => {
      machine.transition(ANALYSIS_STATUS.ANALYZING);
      machine.transition(ANALYSIS_STATUS.COMPLETED);
      
      machine.reset();
      
      expect(machine.getState()).toBe(ANALYSIS_STATUS.IDLE);
    });
  });
});

describe('StateMachineManager', () => {
  let manager;
  
  beforeEach(() => {
    manager = new StateMachineManager();
  });
  
  test('应该创建新的状态机', () => {
    const machine = manager.getOrCreate('analysis-001');
    expect(machine).toBeInstanceOf(AnalysisStateMachine);
    expect(machine.analysisId).toBe('analysis-001');
  });
  
  test('应该返回已存在的状态机', () => {
    const machine1 = manager.getOrCreate('analysis-001');
    const machine2 = manager.getOrCreate('analysis-001');
    expect(machine1).toBe(machine2);
  });
  
  test('应该能够获取活动中的分析任务', () => {
    const m1 = manager.getOrCreate('analysis-001');
    const m2 = manager.getOrCreate('analysis-002');
    
    m1.transition(ANALYSIS_STATUS.ANALYZING);
    m2.transition(ANALYSIS_STATUS.COMPLETED);
    
    const active = manager.getActiveAnalysisIds();
    expect(active).toContain('analysis-001');
    expect(active).not.toContain('analysis-002');
  });
});
