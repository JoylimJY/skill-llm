/**
 * 模板方法模式（Template Method Pattern）
 * 
 * 定义第一性原理分析的 7 阶段骨架
 * 各策略可以重写特定步骤，但整体流程保持一致
 */

const { AnalysisStrategy } = require('./strategies/strategy');

class FirstPrincipleAnalyzer {
  /**
   * @param {AnalysisStrategy} strategy - 分析策略
   */
  constructor(strategy) {
    if (!(strategy instanceof AnalysisStrategy)) {
      throw new Error('strategy must be an instance of AnalysisStrategy');
    }
    this.strategy = strategy;
    this.state = {
      problem: '',
      assumptions: [],
      whyChain: [],
      fundamentalTruths: [],
      solutions: [],
      comparison: {}
    };
  }

  /**
   * 模板方法：执行完整分析流程
   * @param {string} problem - 问题描述
   * @returns {object} 分析报告
   */
  analyze(problem) {
    this.state.problem = problem;
    
    // 阶段 1：问题分类（已预先完成）
    this.classifyProblem(problem);
    
    // 阶段 2：假设识别与质疑
    this.identifyAndChallengeAssumptions(problem);
    
    // 阶段 3：逐层分解（5Why）
    this.decomposeWithFiveWhys(problem);
    
    // 阶段 4：基本真理验证
    this.verifyFundamentalTruths();
    
    // 阶段 5：重构方案生成
    this.generateSolutions();
    
    // 阶段 6：类比方案对比
    this.compareWithTraditionalApproaches();
    
    // 阶段 7：生成报告
    return this.generateReport();
  }

  classifyProblem(problem) {
    // 由策略决定分类逻辑（可重写）
    this.state.category = this.strategy.getName();
  }

  identifyAndChallengeAssumptions(problem) {
    this.state.assumptions = this.strategy.identifyAssumptions(problem);
  }

  decomposeWithFiveWhys(problem) {
    this.state.whyChain = [];
    for (let level = 1; level <= 5; level++) {
      this.state.whyChain.push({
        level,
        question: this.strategy.getWhyQuestion(problem, level),
        answer: null // 由用户交互填充
      });
    }
  }

  verifyFundamentalTruths() {
    this.state.truthCriteria = this.strategy.getTruthVerificationCriteria();
  }

  generateSolutions() {
    this.state.solutions = this.strategy.generateSolutions(this.state.fundamentalTruths);
  }

  compareWithTraditionalApproaches() {
    this.state.comparison.dimensions = this.strategy.getComparisonDimensions();
  }

  generateReport() {
    return {
      category: this.state.category,
      problem: this.state.problem,
      assumptions: this.state.assumptions,
      whyChain: this.state.whyChain,
      truthCriteria: this.state.truthCriteria,
      fundamentalTruths: this.state.fundamentalTruths,
      solutions: this.state.solutions,
      comparison: this.state.comparison
    };
  }

  /**
   * 填充 5Why 答案
   * @param {number} level - 层级
   * @param {string} answer - 答案
   */
  setWhyAnswer(level, answer) {
    if (this.state.whyChain[level - 1]) {
      this.state.whyChain[level - 1].answer = answer;
      
      // 如果到达第 5 层，提取基本真理
      if (level === 5) {
        this.state.fundamentalTruths = [answer];
      }
    }
  }
}

module.exports = { FirstPrincipleAnalyzer };
