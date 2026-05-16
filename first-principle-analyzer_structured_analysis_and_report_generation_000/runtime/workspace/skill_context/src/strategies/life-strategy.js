/**
 * 人生决策分析策略
 */
const { AnalysisStrategy } = require('./strategy');

class LifeStrategy extends AnalysisStrategy {
  getName() { return '人生决策分析'; }

  identifyAssumptions(problem) {
    return [
      { assumption: '必须做出非此即彼的选择', challenge: '为什么不能两者兼得？是否有第三条路？' },
      { assumption: '现在是做决定的最佳时机', challenge: '为什么现在必须决定？延迟决策的成本是什么？' },
      { assumption: '社会期望的路径是正确的', challenge: '社会期望是基于你的情况，还是普遍模板？' },
      { assumption: '一次选择决定一生', challenge: '这个选择真的不可逆吗？转换成本有多高？' }
    ];
  }

  getWhyQuestion(problem, level) {
    const questions = [
      '为什么这个问题对你重要？它触及什么核心价值观？',
      '为什么你认为这是关键选择？背后是什么恐惧或渴望？',
      '为什么你相信这个选项更好？证据是什么？',
      '为什么你限制了自己的选择？有哪些隐藏的可能性？',
      '从人的本质层面，什么是真正重要的？'
    ];
    return questions[level - 1] || questions[questions.length - 1];
  }

  getTruthVerificationCriteria() {
    return [
      '这个真理是否符合你的核心价值观？',
      '这个真理在 10 年后回顾是否仍然正确？',
      '这个真理是否独立于他人期望？',
      '这个真理是否让你更接近理想中的自己？'
    ];
  }

  generateSolutions(fundamentalTruths) {
    return [
      { name: '最小遗憾路径', description: '选择 80 岁时回顾最不会后悔的选项', pros: ['长期视角', '减少后悔'], cons: ['短期可能痛苦'] },
      { name: '能力复利路径', description: '选择能持续积累能力和资源的选项', pros: ['长期增值', '抗风险'], cons: ['短期回报低'] },
      { name: '组合策略', description: '主业保底 + 副业探索，降低风险', pros: ['风险分散', '探索自由'], cons: ['精力分散'] }
    ];
  }

  getComparisonDimensions() {
    return ['长期满意度', '能力成长', '财务回报', '工作生活平衡', '社会影响', '个人意义'];
  }
}

module.exports = { LifeStrategy };
