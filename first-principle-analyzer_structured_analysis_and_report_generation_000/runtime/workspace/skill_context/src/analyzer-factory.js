/**
 * 工厂模式（Factory Pattern）
 * 
 * 根据问题类型自动创建对应的分析器
 */

const { FirstPrincipleAnalyzer } = require('./template-method');
const { TechnicalStrategy } = require('./strategies/technical-strategy');
const { BusinessStrategy } = require('./strategies/business-strategy');
const { LifeStrategy } = require('./strategies/life-strategy');
const { AcademicStrategy } = require('./strategies/academic-strategy');

class AnalyzerFactory {
  /**
   * 问题类型关键词映射
   */
  static KEYWORD_MAP = {
    technical: ['技术', '架构', '系统', '代码', '开发', '软件', '平台', 'API', '数据库', '性能'],
    business: ['商业', '市场', '产品', '盈利', '竞争', '投资', '创业', '增长', '用户', '收入'],
    life: ['人生', '职业', '选择', '工作', '生活', '家庭', '健康', '学习', '成长', '幸福'],
    academic: ['研究', '学术', '论文', '理论', '实验', '数据', '文献', '期刊', '学科', '知识']
  };

  /**
   * 根据问题文本自动检测类型
   * @param {string} problem - 问题描述
   * @returns {string} 类型
   */
  static detectType(problem) {
    const scores = { technical: 0, business: 0, life: 0, academic: 0 };
    
    for (const [type, keywords] of Object.entries(this.KEYWORD_MAP)) {
      for (const keyword of keywords) {
        if (problem.includes(keyword)) {
          scores[type]++;
        }
      }
    }

    const maxType = Object.entries(scores)
      .sort((a, b) => b[1] - a[1])[0];
    
    return maxType[1] > 0 ? maxType[0] : 'technical'; // 默认技术类
  }

  /**
   * 创建分析器
   * @param {string} type - 类型（technical/business/life/academic）
   * @returns {FirstPrincipleAnalyzer}
   */
  static createAnalyzer(type) {
    const strategies = {
      technical: TechnicalStrategy,
      business: BusinessStrategy,
      life: LifeStrategy,
      academic: AcademicStrategy
    };

    const StrategyClass = strategies[type];
    if (!StrategyClass) {
      throw new Error(`Unknown strategy type: ${type}`);
    }

    return new FirstPrincipleAnalyzer(new StrategyClass());
  }

  /**
   * 智能创建分析器（自动检测类型）
   * @param {string} problem - 问题描述
   * @returns {{analyzer: FirstPrincipleAnalyzer, detectedType: string}}
   */
  static createSmartAnalyzer(problem) {
    const detectedType = this.detectType(problem);
    return {
      analyzer: this.createAnalyzer(detectedType),
      detectedType
    };
  }
}

module.exports = { AnalyzerFactory };
