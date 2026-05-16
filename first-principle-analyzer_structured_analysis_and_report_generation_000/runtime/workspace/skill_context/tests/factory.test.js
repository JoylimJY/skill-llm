/**
 * 工厂模式测试
 */

const { AnalyzerFactory } = require('../src/analyzer-factory');
const { FirstPrincipleAnalyzer } = require('../src/template-method');

describe('Factory Pattern - AnalyzerFactory', () => {
  describe('detectType', () => {
    test('should detect technical problems', () => {
      expect(AnalyzerFactory.detectType('如何设计一个更好的系统架构？')).toBe('technical');
      expect(AnalyzerFactory.detectType('这个代码性能有问题')).toBe('technical');
    });

    test('should detect business problems', () => {
      expect(AnalyzerFactory.detectType('是否应该进入新市场？')).toBe('business');
      expect(AnalyzerFactory.detectType('如何提高产品收入？')).toBe('business');
    });

    test('should detect life problems', () => {
      // "创业" contains business keywords, so it's detected as business
      // Use clearer life-related questions
      expect(AnalyzerFactory.detectType('如何平衡工作与生活？')).toBe('life');
      expect(AnalyzerFactory.detectType('职业选择困惑，不知道要不要换工作')).toBe('life');
    });

    test('should detect academic problems', () => {
      expect(AnalyzerFactory.detectType('这个研究方向有前景吗？')).toBe('academic');
      expect(AnalyzerFactory.detectType('如何发表论文？')).toBe('academic');
    });

    test('should default to technical for unknown problems', () => {
      expect(AnalyzerFactory.detectType('这是一个模糊的问题')).toBe('technical');
    });
  });

  describe('createAnalyzer', () => {
    test('should create technical analyzer', () => {
      const analyzer = AnalyzerFactory.createAnalyzer('technical');
      expect(analyzer).toBeInstanceOf(FirstPrincipleAnalyzer);
    });

    test('should create business analyzer', () => {
      const analyzer = AnalyzerFactory.createAnalyzer('business');
      expect(analyzer).toBeInstanceOf(FirstPrincipleAnalyzer);
    });

    test('should create life analyzer', () => {
      const analyzer = AnalyzerFactory.createAnalyzer('life');
      expect(analyzer).toBeInstanceOf(FirstPrincipleAnalyzer);
    });

    test('should create academic analyzer', () => {
      const analyzer = AnalyzerFactory.createAnalyzer('academic');
      expect(analyzer).toBeInstanceOf(FirstPrincipleAnalyzer);
    });

    test('should throw error for unknown type', () => {
      expect(() => AnalyzerFactory.createAnalyzer('unknown')).toThrow('Unknown strategy type');
    });
  });

  describe('createSmartAnalyzer', () => {
    test('should auto-detect and create analyzer', () => {
      const result = AnalyzerFactory.createSmartAnalyzer('如何设计一个更好的系统？');
      expect(result).toHaveProperty('analyzer');
      expect(result).toHaveProperty('detectedType');
      expect(result.detectedType).toBe('technical');
      expect(result.analyzer).toBeInstanceOf(FirstPrincipleAnalyzer);
    });

    test('should detect business type', () => {
      const result = AnalyzerFactory.createSmartAnalyzer('是否应该创业？');
      expect(result.detectedType).toBe('business');
    });

    test('should detect life type', () => {
      const result = AnalyzerFactory.createSmartAnalyzer('职业选择困惑');
      expect(result.detectedType).toBe('life');
    });
  });
});
