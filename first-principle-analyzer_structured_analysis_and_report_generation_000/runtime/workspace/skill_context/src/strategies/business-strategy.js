/**
 * 商业决策分析策略
 */
const { AnalysisStrategy } = require('./strategy');

class BusinessStrategy extends AnalysisStrategy {
  getName() { return '商业决策分析'; }

  identifyAssumptions(problem) {
    return [
      { assumption: '必须进入这个市场才能增长', challenge: '为什么必须进入？现有市场的深度挖掘是否更优？' },
      { assumption: '竞争对手的做法是正确参考', challenge: '对手的成功是因为策略正确，还是时机/运气？' },
      { assumption: '需要大量资金才能启动', challenge: '为什么需要这么多资金？精益启动是否可行？' },
      { assumption: '规模是成功的关键指标', challenge: '规模是手段还是目的？盈利质量是否更重要？' }
    ];
  }

  getWhyQuestion(problem, level) {
    const questions = [
      '为什么这个商业机会存在？用户真正需要什么？',
      '为什么用户愿意付费？价值主张是什么？',
      '为什么是我们来做？竞争优势在哪里？',
      '为什么现在是好时机？市场窗口期多长？',
      '从经济学层面，什么是可持续的盈利模式？'
    ];
    return questions[level - 1] || questions[questions.length - 1];
  }

  getTruthVerificationCriteria() {
    return [
      '这个真理是否有数据支撑？',
      '这个真理是否独立于具体商业模式？',
      '这个真理在经济下行时是否仍然成立？',
      '这个真理是否可以被量化验证？'
    ];
  }

  generateSolutions(fundamentalTruths) {
    return [
      { name: '精益创业模式', description: 'MVP 快速验证，基于反馈迭代', pros: ['降低风险', '快速学习'], cons: ['可能错过窗口'] },
      { name: '平台模式', description: '构建双边/多边市场，网络效应驱动', pros: ['高壁垒', '规模效应'], cons: ['冷启动难'] },
      { name: '利基市场深耕', description: '聚焦细分领域，做到极致', pros: ['竞争少', '用户忠诚'], cons: ['市场天花板'] }
    ];
  }

  getComparisonDimensions() {
    return ['市场规模', '增长速度', '竞争强度', '盈利模式', '进入壁垒', '单位经济'];
  }
}

module.exports = { BusinessStrategy };
