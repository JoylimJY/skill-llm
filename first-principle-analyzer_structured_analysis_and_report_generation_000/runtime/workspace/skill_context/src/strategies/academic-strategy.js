/**
 * 学术研究分析策略
 */
const { AnalysisStrategy } = require('./strategy');

class AcademicStrategy extends AnalysisStrategy {
  getName() { return '学术研究分析'; }

  identifyAssumptions(problem) {
    return [
      { assumption: '必须遵循传统研究方法', challenge: '为什么必须用这个方法？跨学科方法是否更有价值？' },
      { assumption: '研究必须填补文献空白', challenge: '空白存在是因为重要，还是因为难？' },
      { assumption: '需要完整理论框架才能开始', challenge: '探索性研究是否允许边做边完善理论？' },
      { assumption: '发表是高影响力期刊才是成功', challenge: '影响力只来自期刊等级吗？实际应用价值呢？' }
    ];
  }

  getWhyQuestion(problem, level) {
    const questions = [
      '为什么这个问题值得研究？它对知识/社会有什么贡献？',
      '为什么这个问题尚未解决？是技术限制还是概念混淆？',
      '为什么你的方法能解决这个问题？相比现有方法的优势？',
      '为什么这个研究方向有前景？趋势和证据是什么？',
      '从认识论层面，什么是可知的？什么是可验证的？'
    ];
    return questions[level - 1] || questions[questions.length - 1];
  }

  getTruthVerificationCriteria() {
    return [
      '这个真理是否有实证或逻辑证明支持？',
      '这个真理是否可被同行评审和复现？',
      '这个真理是否独立于特定理论框架？',
      '这个真理是否对后续研究有指导价值？'
    ];
  }

  generateSolutions(fundamentalTruths) {
    return [
      { name: '增量创新路径', description: '在现有研究基础上做小步改进', pros: ['方法成熟', '易发表'], cons: ['影响力有限'] },
      { name: '范式突破路径', description: '挑战现有范式，提出全新框架', pros: ['高影响力', '开创性'], cons: ['高风险'] },
      { name: '交叉学科路径', description: '融合多学科方法，创造新视角', pros: ['创新性高', '竞争少'], cons: ['需要多领域知识'] }
    ];
  }

  getComparisonDimensions() {
    return ['创新性', '可行性', '影响力', '资源需求', '时间周期', '发表潜力'];
  }
}

module.exports = { AcademicStrategy };
