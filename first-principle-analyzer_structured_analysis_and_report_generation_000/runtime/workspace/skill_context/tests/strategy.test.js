/**
 * 策略模式测试
 */

const { TechnicalStrategy } = require('../src/strategies/technical-strategy');
const { BusinessStrategy } = require('../src/strategies/business-strategy');
const { LifeStrategy } = require('../src/strategies/life-strategy');
const { AcademicStrategy } = require('../src/strategies/academic-strategy');

describe('Strategy Pattern', () => {
  describe('TechnicalStrategy', () => {
    let strategy;

    beforeEach(() => {
      strategy = new TechnicalStrategy();
    });

    test('should return correct name', () => {
      expect(strategy.getName()).toBe('技术架构分析');
    });

    test('should identify assumptions', () => {
      const assumptions = strategy.identifyAssumptions('如何设计一个更好的技能系统？');
      expect(assumptions).toHaveLength(4);
      expect(assumptions[0]).toHaveProperty('assumption');
      expect(assumptions[0]).toHaveProperty('challenge');
    });

    test('should return 5Why questions', () => {
      for (let level = 1; level <= 5; level++) {
        const question = strategy.getWhyQuestion('技术问题', level);
        expect(question).toBeDefined();
        expect(question.length).toBeGreaterThan(0);
      }
    });

    test('should return truth verification criteria', () => {
      const criteria = strategy.getTruthVerificationCriteria();
      expect(criteria).toHaveLength(4);
    });

    test('should generate solutions', () => {
      const solutions = strategy.generateSolutions(['真理 1', '真理 2']);
      expect(solutions).toHaveLength(3);
      expect(solutions[0]).toHaveProperty('name');
      expect(solutions[0]).toHaveProperty('description');
      expect(solutions[0]).toHaveProperty('pros');
      expect(solutions[0]).toHaveProperty('cons');
    });

    test('should return comparison dimensions', () => {
      const dimensions = strategy.getComparisonDimensions();
      expect(dimensions).toHaveLength(6);
    });
  });

  describe('BusinessStrategy', () => {
    let strategy;

    beforeEach(() => {
      strategy = new BusinessStrategy();
    });

    test('should return correct name', () => {
      expect(strategy.getName()).toBe('商业决策分析');
    });

    test('should identify assumptions', () => {
      const assumptions = strategy.identifyAssumptions('是否应该进入新市场？');
      expect(assumptions).toHaveLength(4);
    });

    test('should generate solutions', () => {
      const solutions = strategy.generateSolutions(['市场需求真实存在']);
      expect(solutions).toHaveLength(3);
      expect(solutions.map(s => s.name)).toContain('精益创业模式');
    });
  });

  describe('LifeStrategy', () => {
    let strategy;

    beforeEach(() => {
      strategy = new LifeStrategy();
    });

    test('should return correct name', () => {
      expect(strategy.getName()).toBe('人生决策分析');
    });

    test('should identify assumptions about choices', () => {
      const assumptions = strategy.identifyAssumptions('应该换工作还是创业？');
      expect(assumptions.some(a => a.assumption.includes('非此即彼'))).toBe(true);
    });
  });

  describe('AcademicStrategy', () => {
    let strategy;

    beforeEach(() => {
      strategy = new AcademicStrategy();
    });

    test('should return correct name', () => {
      expect(strategy.getName()).toBe('学术研究分析');
    });

    test('should identify research assumptions', () => {
      const assumptions = strategy.identifyAssumptions('这个研究方向有前景吗？');
      expect(assumptions).toHaveLength(4);
    });
  });
});
