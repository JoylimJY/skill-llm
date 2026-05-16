/**
 * 构建器模式（Builder Pattern）
 * 
 * 链式 API 构建结构化分析报告
 */

class ReportBuilder {
  constructor() {
    this.report = {
      title: '',
      metadata: {},
      sections: []
    };
  }

  setTitle(title) {
    this.report.title = title;
    return this;
  }

  setMetadata(metadata) {
    this.report.metadata = {
      ...this.report.metadata,
      ...metadata
    };
    return this;
  }

  addSection(section) {
    this.report.sections.push(section);
    return this;
  }

  addExecutiveSummary(summary) {
    this.report.sections.unshift({
      type: 'executive_summary',
      title: '执行摘要',
      content: summary
    });
    return this;
  }

  addProblemSection(problem, category) {
    this.report.sections.push({
      type: 'problem',
      title: '问题分析',
      content: { problem, category }
    });
    return this;
  }

  addAssumptionsSection(assumptions) {
    this.report.sections.push({
      type: 'assumptions',
      title: '假设识别与质疑',
      content: assumptions
    });
    return this;
  }

  addWhyChainSection(whyChain) {
    this.report.sections.push({
      type: 'why_chain',
      title: '5Why 分解链',
      content: whyChain
    });
    return this;
  }

  addTruthsSection(truths, criteria) {
    this.report.sections.push({
      type: 'fundamental_truths',
      title: '基本真理',
      content: { truths, criteria }
    });
    return this;
  }

  addSolutionsSection(solutions) {
    this.report.sections.push({
      type: 'solutions',
      title: '重构方案',
      content: solutions
    });
    return this;
  }

  addComparisonSection(comparison) {
    this.report.sections.push({
      type: 'comparison',
      title: '与传统方案对比',
      content: comparison
    });
    return this;
  }

  build() {
    return this.report;
  }

  /**
   * 构建 Markdown 格式报告
   * @returns {string}
   */
  toMarkdown() {
    let md = `# ${this.report.title}\n\n`;
    
    // 元数据
    if (Object.keys(this.report.metadata).length > 0) {
      md += `**分析时间**: ${new Date().toISOString()}\n`;
      md += `**分析类型**: ${this.report.metadata.category || '通用'}\n\n`;
    }

    // 各章节
    for (const section of this.report.sections) {
      md += `## ${section.title}\n\n`;
      md += this._sectionToMarkdown(section);
      md += '\n---\n\n';
    }

    return md;
  }

  _sectionToMarkdown(section) {
    switch (section.type) {
      case 'executive_summary':
        return section.content;
      
      case 'problem':
        return `**问题**: ${section.content.problem}\n\n**分类**: ${section.content.category}`;
      
      case 'assumptions':
        return section.content.map((item, i) => 
          `**假设${i+1}**: ${item.assumption}\n\n**质疑**: ${item.challenge}\n`
        ).join('\n');
      
      case 'why_chain':
        return section.content.map(item => 
          `**Q${item.level}**: ${item.question}\n\n**A**: ${item.answer || '待填充'}\n`
        ).join('\n');
      
      case 'fundamental_truths':
        let truthMd = '**验证标准**:\n';
        section.content.criteria.forEach((c, i) => truthMd += `${i+1}. ${c}\n`);
        truthMd += '\n**基本真理**:\n';
        section.content.truths.forEach((t, i) => truthMd += `${i+1}. ${t}\n`);
        return truthMd;
      
      case 'solutions':
        return section.content.map(sol => 
          `### ${sol.name}\n\n${sol.description}\n\n**优势**: ${sol.pros.join('、')}\n\n**劣势**: ${sol.cons.join('、')}\n`
        ).join('\n');
      
      case 'comparison':
        return `**对比维度**: ${section.content.dimensions.join('、')}`;
      
      default:
        return JSON.stringify(section.content, null, 2);
    }
  }
}

module.exports = { ReportBuilder };
