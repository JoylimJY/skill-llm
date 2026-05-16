/**
 * Observer 测试
 */

const {
  ANALYSIS_EVENTS,
  Observer,
  LoggerObserver,
  ProgressObserver,
  NotificationObserver,
  AnalysisEventEmitter,
  createStateChangedEvent,
  createProgressUpdatedEvent
} = require('../src/observer');

describe('Observer', () => {
  test('Observer 基类应该抛出错误', () => {
    const observer = new Observer();
    expect(() => observer.update('test', {})).toThrow('必须实现 update 方法');
  });
});

describe('LoggerObserver', () => {
  test('应该记录事件', () => {
    const observer = new LoggerObserver({ prefix: '[Test]' });
    
    // 不抛出错误即成功
    expect(() => {
      observer.update('test_event', { data: 'test' });
    }).not.toThrow();
  });
});

describe('ProgressObserver', () => {
  test('应该追踪进度', () => {
    const observer = new ProgressObserver();
    
    observer.update(ANALYSIS_EVENTS.PROGRESS_UPDATED, {
      progress: 50,
      stage: 'decomposition'
    });
    
    const progress = observer.getProgress();
    expect(progress.progress).toBe(50);
    expect(progress.stage).toBe('decomposition');
  });
});

describe('NotificationObserver', () => {
  test('应该收集通知', () => {
    const observer = new NotificationObserver();
    
    observer.update('event1', { data: 'test1' });
    observer.update('event2', { data: 'test2' });
    
    const notifications = observer.getNotifications();
    expect(notifications.length).toBe(2);
  });
  
  test('应该能够清除通知', () => {
    const observer = new NotificationObserver();
    observer.update('event1', {});
    observer.clearNotifications();
    
    expect(observer.getNotifications().length).toBe(0);
  });
  
  test('禁用时不应该收集通知', () => {
    const observer = new NotificationObserver({ enabled: false });
    observer.update('event1', {});
    
    expect(observer.getNotifications().length).toBe(0);
  });
});

describe('AnalysisEventEmitter', () => {
  let emitter;
  
  beforeEach(() => {
    emitter = new AnalysisEventEmitter();
  });
  
  test('应该能够订阅事件', () => {
    const observer = new LoggerObserver();
    emitter.subscribe('test_event', observer);
    
    expect(emitter.getObserverCount('test_event')).toBe(1);
  });
  
  test('应该能够发布事件给观察者', () => {
    const received = [];
    const observer = new (class extends Observer {
      update(event, data) { received.push({ event, data }); }
    })();
    
    emitter.subscribe('test_event', observer);
    emitter.publish('test_event', { value: 123 });
    
    expect(received.length).toBe(1);
    expect(received[0].event).toBe('test_event');
    expect(received[0].data.value).toBe(123);
  });
  
  test('应该能够取消订阅', () => {
    const observer = new LoggerObserver();
    emitter.subscribe('test_event', observer);
    emitter.unsubscribe('test_event', observer);
    
    expect(emitter.getObserverCount('test_event')).toBe(0);
  });
  
  test('应该能够清除所有观察者', () => {
    emitter.subscribe('event1', new LoggerObserver());
    emitter.subscribe('event2', new LoggerObserver());
    emitter.clear();
    
    expect(emitter.getObserverCount('event1')).toBe(0);
    expect(emitter.getObserverCount('event2')).toBe(0);
  });
  
  test('观察者抛出错误不应该影响其他观察者', () => {
    const errorObserver = new (class extends Observer {
      update() { throw new Error('测试错误'); }
    })();
    
    const received = [];
    const goodObserver = new (class extends Observer {
      update(event, data) { received.push({ event, data }); }
    })();
    
    emitter.subscribe('test_event', errorObserver);
    emitter.subscribe('test_event', goodObserver);
    
    expect(() => {
      emitter.publish('test_event', {});
    }).not.toThrow();
    
    expect(received.length).toBe(1);
  });
});

describe('事件辅助函数', () => {
  test('应该创建状态变更事件', () => {
    const event = createStateChangedEvent('idle', 'analyzing', 'test-001');
    
    expect(event.fromState).toBe('idle');
    expect(event.toState).toBe('analyzing');
    expect(event.analysisId).toBe('test-001');
    expect(event.timestamp).toBeDefined();
  });
  
  test('应该创建进度更新事件', () => {
    const event = createProgressUpdatedEvent(75, 'verify', 'test-001');
    
    expect(event.progress).toBe(75);
    expect(event.stage).toBe('verify');
    expect(event.analysisId).toBe('test-001');
  });
});
