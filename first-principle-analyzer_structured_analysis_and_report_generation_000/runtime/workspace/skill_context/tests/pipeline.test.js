/**
 * Pipeline 测试
 */

const {
  Processor,
  ProblemReceiveProcessor,
  AssumptionIdentifyProcessor,
  DecompositionProcessor,
  AnalysisPipeline,
  PipelineBuilder
} = require('../src/pipeline');

describe('Processor', () => {
  class TestProcessor extends Processor {
    handle(context) {
      context.processed = true;
      return this.passToNext(context);
    }
  }
  
  test('应该能够设置下一个处理器', () => {
    const p1 = new TestProcessor('p1');
    const p2 = new TestProcessor('p2');
    
    p1.setNext(p2);
    expect(p1.next).toBe(p2);
  });
  
  test('应该支持链式调用', () => {
    const p1 = new TestProcessor('p1');
    const p2 = new TestProcessor('p2');
    const p3 = new TestProcessor('p3');
    
    const result = p1.setNext(p2).setNext(p3);
    expect(result).toBe(p3);
  });
});

describe('AnalysisPipeline', () => {
  test('应该能够添加处理器', () => {
    const pipeline = new AnalysisPipeline();
    pipeline.add(new ProblemReceiveProcessor());
    
    expect(pipeline.getProcessorNames()).toEqual(['problem_receive']);
  });
  
  test('应该能够执行处理器链', () => {
    const pipeline = new AnalysisPipeline();
    pipeline
      .add(new ProblemReceiveProcessor())
      .add(new AssumptionIdentifyProcessor());
    
    const result = pipeline.execute({ problem: '测试问题' });
    
    expect(result.problem).toBe('测试问题');
    expect(result.processorsExecuted).toEqual(['problem_receive', 'assumption_identify']);
    expect(result.pipelineCompletedAt).toBeDefined();
  });
  
  test('空管道应该抛出错误', () => {
    const pipeline = new AnalysisPipeline();
    
    expect(() => pipeline.execute({})).toThrow('管道为空');
  });
});

describe('PipelineBuilder', () => {
  test('应该能够构建标准管道', () => {
    const builder = new PipelineBuilder();
    const pipeline = builder.buildStandard();
    
    const names = pipeline.getProcessorNames();
    expect(names.length).toBe(7);
    expect(names[0]).toBe('problem_receive');
    expect(names[names.length - 1]).toBe('report_generate');
  });
  
  test('应该支持链式构建', () => {
    const pipeline = new PipelineBuilder()
      .withProblemReceive()
      .withAssumptionIdentify()
      .withDecomposition()
      .build();
    
    expect(pipeline.getProcessorNames()).toEqual([
      'problem_receive',
      'assumption_identify',
      'decomposition'
    ]);
  });
});

describe('处理器流程', () => {
  test('应该按顺序执行所有处理器', () => {
    const pipeline = new PipelineBuilder()
      .withProblemReceive()
      .withAssumptionIdentify()
      .withAssumptionQuestion()
      .withDecomposition()
      .withTruthVerify()
      .withReconstruct()
      .withReportGenerate()
      .build();
    
    const result = pipeline.execute({ problem: '完整测试' });
    
    expect(result.stage).toBe('report_generate');
    expect(result.processorsExecuted.length).toBe(7);
    expect(result.pipelineStartedAt).toBeDefined();
    expect(result.pipelineCompletedAt).toBeDefined();
  });
});
