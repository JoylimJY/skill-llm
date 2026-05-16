/**
 * Pipeline - 责任链模式实现
 * 
 * 构建可组合的分析处理管道
 * 灵感来源：meta-skill-weaver 状态持久化系统
 * 
 * 设计模式：责任链模式 (Chain of Responsibility)
 * - 将处理逻辑拆分为独立的处理器
 * - 处理器可以动态组合
 * - 支持中途退出和错误处理
 */

// ============================================================
// 处理器基类
// ============================================================

/**
 * 处理器基类
 * 所有处理器必须继承此类
 */
class Processor {
  constructor(name) {
    this.name = name;
    this.next = null;
  }
  
  /**
   * 设置下一个处理器
   * @param {Processor} processor - 下一个处理器
   * @returns {Processor} 当前处理器（支持链式调用）
   */
  setNext(processor) {
    this.next = processor;
    return processor;
  }
  
  /**
   * 处理请求
   * @param {Object} context - 处理上下文
   * @returns {Object} 处理结果
   */
  handle(context) {
    throw new Error('子类必须实现 handle 方法');
  }
  
  /**
   * 传递给下一个处理器
   * @param {Object} context - 处理上下文
   * @returns {Object} 最终结果
   */
  passToNext(context) {
    if (this.next) {
      return this.next.handle(context);
    }
    return context;
  }
}

// ============================================================
// 具体处理器实现
// ============================================================

/**
 * 问题接收处理器
 */
class ProblemReceiveProcessor extends Processor {
  constructor() {
    super('problem_receive');
  }
  
  handle(context) {
    console.log(`[Pipeline] 处理器 ${this.name}: 接收问题`);
    context.stage = 'problem_receive';
    context.receivedAt = new Date().toISOString();
    return this.passToNext(context);
  }
}

/**
 * 假设识别处理器
 */
class AssumptionIdentifyProcessor extends Processor {
  constructor() {
    super('assumption_identify');
  }
  
  handle(context) {
    console.log(`[Pipeline] 处理器 ${this.name}: 识别假设`);
    context.stage = 'assumption_identify';
    context.assumptions = context.assumptions || [];
    return this.passToNext(context);
  }
}

/**
 * 假设质疑处理器
 */
class AssumptionQuestionProcessor extends Processor {
  constructor() {
    super('assumption_question');
  }
  
  handle(context) {
    console.log(`[Pipeline] 处理器 ${this.name}: 质疑假设`);
    context.stage = 'assumption_question';
    context.questionedAssumptions = context.assumptions?.map(a => ({
      ...a,
      questioned: true,
      questionedAt: new Date().toISOString()
    })) || [];
    return this.passToNext(context);
  }
}

/**
 * 问题分解处理器
 */
class DecompositionProcessor extends Processor {
  constructor() {
    super('decomposition');
  }
  
  handle(context) {
    console.log(`[Pipeline] 处理器 ${this.name}: 分解问题`);
    context.stage = 'decomposition';
    context.layers = context.layers || [];
    return this.passToNext(context);
  }
}

/**
 * 真理验证处理器
 */
class TruthVerifyProcessor extends Processor {
  constructor() {
    super('truth_verify');
  }
  
  handle(context) {
    console.log(`[Pipeline] 处理器 ${this.name}: 验证真理`);
    context.stage = 'truth_verify';
    context.basicTruths = context.basicTruths || [];
    context.verifiedAt = new Date().toISOString();
    return this.passToNext(context);
  }
}

/**
 * 方案重构处理器
 */
class ReconstructProcessor extends Processor {
  constructor() {
    super('reconstruct');
  }
  
  handle(context) {
    console.log(`[Pipeline] 处理器 ${this.name}: 重构方案`);
    context.stage = 'reconstruct';
    context.solution = context.solution || {};
    context.reconstructedAt = new Date().toISOString();
    return this.passToNext(context);
  }
}

/**
 * 报告生成处理器
 */
class ReportGenerateProcessor extends Processor {
  constructor() {
    super('report_generate');
  }
  
  handle(context) {
    console.log(`[Pipeline] 处理器 ${this.name}: 生成报告`);
    context.stage = 'report_generate';
    context.report = context.report || { content: '', format: 'markdown' };
    context.generatedAt = new Date().toISOString();
    return context; // 最后一个处理器，不传递
  }
}

// ============================================================
// 管道构建器
// ============================================================

/**
 * 分析管道
 * 管理处理器链的执行
 */
class AnalysisPipeline {
  constructor() {
    this.processors = [];
    this.head = null;
  }
  
  /**
   * 添加处理器
   * @param {Processor} processor - 处理器实例
   * @returns {AnalysisPipeline} 当前管道（支持链式调用）
   */
  add(processor) {
    this.processors.push(processor);
    
    if (this.processors.length === 1) {
      this.head = processor;
    } else {
      this.processors[this.processors.length - 2].setNext(processor);
    }
    
    return this;
  }
  
  /**
   * 执行管道
   * @param {Object} initialContext - 初始上下文
   * @returns {Object} 最终结果
   */
  execute(initialContext) {
    if (!this.head) {
      throw new Error('管道为空，无法执行');
    }
    
    console.log('[Pipeline] 开始执行分析管道');
    const context = {
      ...initialContext,
      pipelineStartedAt: new Date().toISOString(),
      processorsExecuted: []
    };
    
    try {
      const result = this.head.handle(context);
      result.pipelineCompletedAt = new Date().toISOString();
      result.processorsExecuted = this.processors.map(p => p.name);
      console.log('[Pipeline] 分析管道执行完成');
      return result;
    } catch (error) {
      console.error('[Pipeline] 管道执行失败:', error);
      throw error;
    }
  }
  
  /**
   * 获取处理器列表
   * @returns {Array<string>} 处理器名称列表
   */
  getProcessorNames() {
    return this.processors.map(p => p.name);
  }
  
  /**
   * 重置管道
   */
  reset() {
    this.processors = [];
    this.head = null;
  }
}

/**
 * 管道构建器
 * 提供便捷的管道创建方法
 */
class PipelineBuilder {
  constructor() {
    this.pipeline = new AnalysisPipeline();
  }
  
  /**
   * 添加问题接收处理器
   * @returns {PipelineBuilder} 当前构建器
   */
  withProblemReceive() {
    this.pipeline.add(new ProblemReceiveProcessor());
    return this;
  }
  
  /**
   * 添加假设识别处理器
   * @returns {PipelineBuilder} 当前构建器
   */
  withAssumptionIdentify() {
    this.pipeline.add(new AssumptionIdentifyProcessor());
    return this;
  }
  
  /**
   * 添加假设质疑处理器
   * @returns {PipelineBuilder} 当前构建器
   */
  withAssumptionQuestion() {
    this.pipeline.add(new AssumptionQuestionProcessor());
    return this;
  }
  
  /**
   * 添加问题分解处理器
   * @returns {PipelineBuilder} 当前构建器
   */
  withDecomposition() {
    this.pipeline.add(new DecompositionProcessor());
    return this;
  }
  
  /**
   * 添加真理验证处理器
   * @returns {PipelineBuilder} 当前构建器
   */
  withTruthVerify() {
    this.pipeline.add(new TruthVerifyProcessor());
    return this;
  }
  
  /**
   * 添加方案重构处理器
   * @returns {PipelineBuilder} 当前构建器
   */
  withReconstruct() {
    this.pipeline.add(new ReconstructProcessor());
    return this;
  }
  
  /**
   * 添加报告生成处理器
   * @returns {PipelineBuilder} 当前构建器
   */
  withReportGenerate() {
    this.pipeline.add(new ReportGenerateProcessor());
    return this;
  }
  
  /**
   * 构建完整管道
   * @returns {AnalysisPipeline} 构建的管道
   */
  build() {
    return this.pipeline;
  }
  
  /**
   * 构建标准分析管道（包含所有处理器）
   * @returns {AnalysisPipeline} 标准管道
   */
  buildStandard() {
    return new PipelineBuilder()
      .withProblemReceive()
      .withAssumptionIdentify()
      .withAssumptionQuestion()
      .withDecomposition()
      .withTruthVerify()
      .withReconstruct()
      .withReportGenerate()
      .build();
  }
}

module.exports = {
  Processor,
  ProblemReceiveProcessor,
  AssumptionIdentifyProcessor,
  AssumptionQuestionProcessor,
  DecompositionProcessor,
  TruthVerifyProcessor,
  ReconstructProcessor,
  ReportGenerateProcessor,
  AnalysisPipeline,
  PipelineBuilder
};
