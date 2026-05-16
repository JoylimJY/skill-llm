/**
 * 技术架构分析策略
 */
const { AnalysisStrategy } = require('./strategy');

class TechnicalStrategy extends AnalysisStrategy {
  getName() { return '技术架构分析'; }

  identifyAssumptions(problem) {
    return [
      { assumption: '必须使用某种特定技术栈', challenge: '为什么必须用这个技术栈？是团队熟悉度、生态、还是性能需求？' },
      { assumption: '系统必须是集中式架构', challenge: '集中式是技术必然，还是历史沿袭？分布式是否更合适？' },
      { assumption: '需要完整的文档才能开始开发', challenge: '文档是前置条件还是迭代产物？' },
      { assumption: '性能是最重要的考量', challenge: '对于这个场景，开发效率/可维护性是否比性能更重要？' }
    ];
  }

  getWhyQuestion(problem, level) {
    const questions = [
      '为什么需要这个技术系统？它解决什么核心问题？',
      '为什么这个问题需要技术解决方案？非技术方案是否可行？',
      '为什么当前的技术方案不够好？瓶颈在哪里？',
      '为什么这个瓶颈难以突破？是技术限制还是思维限制？',
      '从物理/逻辑层面，什么是真正不可改变的限制？'
    ];
    return questions[level - 1] || questions[questions.length - 1];
  }

  getTruthVerificationCriteria() {
    return [
      '这个真理是否独立于具体技术栈？',
      '这个真理是否符合物理/数学/逻辑的基本规律？',
      '这个真理是否在 5 年后仍然成立？',
      '这个真理是否可以被证伪？'
    ];
  }

  generateSolutions(fundamentalTruths) {
    return [
      { name: '最小可行架构（MVA）', description: '从基本真理出发，只实现核心功能', pros: ['快速验证', '降低技术债务'], cons: ['可能需重构'] },
      { name: '领域驱动设计（DDD）', description: '从业务本质建模，而非技术实现', pros: ['业务对齐', '长期可维护'], cons: ['学习曲线陡峭'] },
      { name: '事件驱动架构', description: '基于事件流而非请求 - 响应', pros: ['高可扩展', '容错性强'], cons: ['调试复杂'] }
    ];
  }

  getComparisonDimensions() {
    return ['性能', '可扩展性', '可维护性', '开发效率', '学习成本', '生态成熟度'];
  }
}

module.exports = { TechnicalStrategy };
