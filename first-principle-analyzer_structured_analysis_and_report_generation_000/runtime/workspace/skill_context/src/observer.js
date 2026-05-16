/**
 * Observer - 观察者模式实现
 * 
 * 实现状态变更的通知机制
 * 灵感来源：meta-skill-weaver 状态持久化系统
 * 
 * 设计模式：观察者模式 (Observer Pattern)
 * - 解耦状态变更与响应逻辑
 * - 支持多个观察者订阅同一事件
 * - 支持动态添加/移除观察者
 */

// ============================================================
// 事件类型定义
// ============================================================

/**
 * 分析事件类型
 */
const ANALYSIS_EVENTS = {
  STATE_CHANGED: 'state_changed',        // 状态变更
  PROGRESS_UPDATED: 'progress_updated',  // 进度更新
  ERROR_OCCURRED: 'error_occurred',      // 发生错误
  ANALYSIS_STARTED: 'analysis_started',  // 分析开始
  ANALYSIS_COMPLETED: 'analysis_completed', // 分析完成
  ANALYSIS_PAUSED: 'analysis_paused',    // 分析暂停
  ANALYSIS_RESUMED: 'analysis_resumed',  // 分析恢复
  REPORT_GENERATED: 'report_generated'   // 报告生成
};

// ============================================================
// 观察者接口
// ============================================================

/**
 * 观察者接口
 * 所有观察者必须实现此接口
 */
class Observer {
  /**
   * 处理事件
   * @param {string} event - 事件类型
   * @param {Object} data - 事件数据
   */
  update(event, data) {
    throw new Error('观察者必须实现 update 方法');
  }
}

// ============================================================
// 具体观察者实现
// ============================================================

/**
 * 日志观察者
 * 记录所有事件到日志
 */
class LoggerObserver extends Observer {
  constructor(options = {}) {
    super();
    this.prefix = options.prefix || '[Observer]';
    this.logLevel = options.logLevel || 'info';
  }
  
  update(event, data) {
    const timestamp = new Date().toISOString();
    const message = `${this.prefix} 事件：${event}, 数据：${JSON.stringify(data)}`;
    
    switch (this.logLevel) {
      case 'debug':
        console.debug(message);
        break;
      case 'info':
        console.info(message);
        break;
      case 'warn':
        console.warn(message);
        break;
      case 'error':
        console.error(message);
        break;
      default:
        console.log(message);
    }
  }
}

/**
 * 进度观察者
 * 追踪分析进度
 */
class ProgressObserver extends Observer {
  constructor() {
    super();
    this.progress = 0;
    this.stage = 'idle';
  }
  
  update(event, data) {
    if (event === ANALYSIS_EVENTS.PROGRESS_UPDATED) {
      this.progress = data.progress || 0;
      this.stage = data.stage || 'unknown';
      console.log(`[Progress] 进度：${this.progress}%, 阶段：${this.stage}`);
    }
  }
  
  getProgress() {
    return { progress: this.progress, stage: this.stage };
  }
}

/**
 * 通知观察者
 * 发送通知（可扩展为邮件、推送等）
 */
class NotificationObserver extends Observer {
  constructor(options = {}) {
    super();
    this.notifications = [];
    this.enabled = options.enabled !== false;
  }
  
  update(event, data) {
    if (!this.enabled) return;
    
    const notification = {
      event,
      data,
      timestamp: new Date().toISOString()
    };
    
    this.notifications.push(notification);
    
    // 这里可以扩展为实际的通知发送逻辑
    console.log(`[Notification] 发送通知：${event}`);
  }
  
  getNotifications() {
    return [...this.notifications];
  }
  
  clearNotifications() {
    this.notifications = [];
  }
}

// ============================================================
// 主题（被观察者）
// ============================================================

/**
 * 分析事件主题
 * 管理观察者的订阅和事件分发
 */
class AnalysisEventEmitter {
  constructor() {
    this.observers = new Map();
  }
  
  /**
   * 订阅事件
   * @param {string} event - 事件类型
   * @param {Observer} observer - 观察者实例
   */
  subscribe(event, observer) {
    if (!(observer instanceof Observer)) {
      throw new Error('观察者必须是 Observer 的实例');
    }
    
    if (!this.observers.has(event)) {
      this.observers.set(event, []);
    }
    
    this.observers.get(event).push(observer);
    console.log(`[EventEmitter] 订阅事件：${event}, 观察者：${observer.constructor.name}`);
  }
  
  /**
   * 取消订阅
   * @param {string} event - 事件类型
   * @param {Observer} observer - 观察者实例
   */
  unsubscribe(event, observer) {
    if (!this.observers.has(event)) return;
    
    const eventObservers = this.observers.get(event);
    const index = eventObservers.indexOf(observer);
    
    if (index > -1) {
      eventObservers.splice(index, 1);
      console.log(`[EventEmitter] 取消订阅：${event}`);
    }
  }
  
  /**
   * 发布事件
   * @param {string} event - 事件类型
   * @param {Object} data - 事件数据
   */
  publish(event, data = {}) {
    console.log(`[EventEmitter] 发布事件：${event}`);
    
    const eventObservers = this.observers.get(event) || [];
    eventObservers.forEach(observer => {
      try {
        observer.update(event, data);
      } catch (error) {
        console.error(`[EventEmitter] 观察者处理事件失败：${error}`);
      }
    });
    
    // 同时通知所有事件的通用观察者（如果有的话）
    const allObservers = this.observers.get('*') || [];
    allObservers.forEach(observer => {
      try {
        observer.update(event, data);
      } catch (error) {
        console.error(`[EventEmitter] 通用观察者处理事件失败：${error}`);
      }
    });
  }
  
  /**
   * 获取事件的观察者数量
   * @param {string} event - 事件类型
   * @returns {number} 观察者数量
   */
  getObserverCount(event) {
    return (this.observers.get(event) || []).length;
  }
  
  /**
   * 清除所有观察者
   */
  clear() {
    this.observers.clear();
  }
}

// ============================================================
// 事件辅助函数
// ============================================================

/**
 * 创建状态变更事件数据
 */
function createStateChangedEvent(fromState, toState, analysisId) {
  return {
    fromState,
    toState,
    analysisId,
    timestamp: new Date().toISOString()
  };
}

/**
 * 创建进度更新事件数据
 */
function createProgressUpdatedEvent(progress, stage, analysisId) {
  return {
    progress,
    stage,
    analysisId,
    timestamp: new Date().toISOString()
  };
}

/**
 * 创建错误事件数据
 */
function createErrorOccurredEvent(error, analysisId) {
  return {
    error: error.message,
    stack: error.stack,
    analysisId,
    timestamp: new Date().toISOString()
  };
}

module.exports = {
  ANALYSIS_EVENTS,
  Observer,
  LoggerObserver,
  ProgressObserver,
  NotificationObserver,
  AnalysisEventEmitter,
  createStateChangedEvent,
  createProgressUpdatedEvent,
  createErrorOccurredEvent
};
