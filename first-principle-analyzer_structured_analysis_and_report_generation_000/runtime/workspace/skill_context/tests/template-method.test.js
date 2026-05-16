/**
 * 模板方法模式测试
 */

const { FirstPrincipleAnalyzer } = require('../src/template-method');
const { TechnicalStrategy } = require('../src/strategies/technical-strategy');

describe('Template Method Pattern', () => {
  let analyzer;

  beforeEach(() => {
    analyzer = new FirstPrincipleAnalyzer(new TechnicalStrategy());
  });

  test('should throw error if strategy is not provided', () => {
    expect(() => new FirstPrincipleAnalyzer(null)).toThrow('must be an instance of AnalysisStrategy');
  });

  test('should execute full analysis flow', () => {
    const report = analyzer.analyze('如何设计一个更好的技能系统？');
    
    expect(report).toHaveProperty('category');
    expect(report).toHaveProperty('problem');
    expect(report).toHaveProperty('assumptions');
    expect(report).toHaveProperty('whyChain');
    expect(report).toHaveProperty('truthCriteria');
    expect(report).toHaveProperty('solutions');
    expect(report).toHaveProperty('comparison');
  });

  test('should classify problem correctly', () => {
    analyzer.analyze('如何设计一个更好的技能系统？');
    expect(analyzer.state.category).toBe('技术架构分析');
  });

  test('should identify assumptions', () => {
    analyzer.analyze('技术问题');
    expect(analyzer.state.assumptions).toHaveLength(4);
  });

  test('should create 5Why chain', () => {
    analyzer.analyze('技术问题');
    expect(analyzer.state.whyChain).toHaveLength(5);
    expect(analyzer.state.whyChain[0].level).toBe(1);
    expect(analyzer.state.whyChain[4].level).toBe(5);
  });

  test('should generate solutions', () => {
    analyzer.analyze('技术问题');
    expect(analyzer.state.solutions).toHaveLength(3);
  });

  test('should allow setting why answers', () => {
    analyzer.analyze('技术问题');
    analyzer.setWhyAnswer(1, '因为需要提高效率');
    expect(analyzer.state.whyChain[0].answer).toBe('因为需要提高效率');
  });

  test('should extract fundamental truth at level 5', () => {
    analyzer.analyze('技术问题');
    analyzer.setWhyAnswer(5, '性能是系统的核心约束');
    expect(analyzer.state.fundamentalTruths).toContain('性能是系统的核心约束');
  });
});
