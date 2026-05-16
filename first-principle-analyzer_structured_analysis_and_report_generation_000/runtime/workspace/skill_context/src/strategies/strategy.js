/**
 * 分析策略接口（Strategy Pattern）
 * 
 * 定义所有分析策略必须实现的接口
 * 每种问题类型（技术/商业/人生/学术）有独立的策略
 */

class AnalysisStrategy {
  getName() {
    throw new Error('getName() must be implemented');
  }

  identifyAssumptions(problem) {
    throw new Error('identifyAssumptions() must be implemented');
  }

  getWhyQuestion(problem, level) {
    throw new Error('getWhyQuestion() must be implemented');
  }

  getTruthVerificationCriteria() {
    throw new Error('getTruthVerificationCriteria() must be implemented');
  }

  generateSolutions(fundamentalTruths) {
    throw new Error('generateSolutions() must be implemented');
  }

  getComparisonDimensions() {
    throw new Error('getComparisonDimensions() must be implemented');
  }
}

module.exports = { AnalysisStrategy };
