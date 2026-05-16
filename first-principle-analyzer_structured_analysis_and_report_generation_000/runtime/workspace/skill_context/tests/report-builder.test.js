/**
 * 构建器模式测试
 */

const { ReportBuilder } = require('../src/report-builder');

describe('Builder Pattern - ReportBuilder', () => {
  let builder;

  beforeEach(() => {
    builder = new ReportBuilder();
  });

  test('should create empty report', () => {
    const report = builder.build();
    expect(report).toHaveProperty('title', '');
    expect(report).toHaveProperty('metadata', {});
    expect(report).toHaveProperty('sections', []);
  });

  test('should support chainable API', () => {
    const result = builder.setTitle('Test');
    expect(result).toBe(builder);
  });

  test('should build report with title', () => {
    builder.setTitle('First Principles Report');
    const report = builder.build();
    expect(report.title).toBe('First Principles Report');
  });

  test('should add metadata', () => {
    builder.setMetadata({ category: 'Technical', author: 'Test' });
    const report = builder.build();
    expect(report.metadata.category).toBe('Technical');
    expect(report.metadata.author).toBe('Test');
  });

  test('should add sections', () => {
    builder
      .setTitle('Test Report')
      .addProblemSection('How to design system?', 'Technical')
      .addAssumptionsSection([{ assumption: 'Assumption 1', challenge: 'Challenge 1' }]);
    
    const report = builder.build();
    expect(report.sections).toHaveLength(2);
    expect(report.sections[0].type).toBe('problem');
    expect(report.sections[1].type).toBe('assumptions');
  });

  test('should add executive summary at beginning', () => {
    builder
      .addSection({ type: 'content', title: 'Content' })
      .addExecutiveSummary('This is summary');
    
    const report = builder.build();
    expect(report.sections[0].type).toBe('executive_summary');
  });

  test('should generate markdown report', () => {
    builder
      .setTitle('Test Report')
      .setMetadata({ category: 'Technical' })
      .addProblemSection('Test problem', 'Technical')
      .addSolutionsSection([
        { name: 'Solution A', description: 'Description', pros: ['Pro 1'], cons: ['Con 1'] }
      ]);
    
    const md = builder.toMarkdown();
    expect(md).toContain('# Test Report');
    expect(md).toContain('## 问题分析');
    expect(md).toContain('## 重构方案');
    expect(md).toContain('Solution A');
  });

  test('should format assumptions in markdown', () => {
    builder.addAssumptionsSection([
      { assumption: 'Assumption 1', challenge: 'Challenge 1' },
      { assumption: 'Assumption 2', challenge: 'Challenge 2' }
    ]);
    
    const md = builder.toMarkdown();
    expect(md).toContain('假设1');
    expect(md).toContain('质疑');
  });

  test('should format why chain in markdown', () => {
    builder.addWhyChainSection([
      { level: 1, question: 'Why?', answer: 'Because A' },
      { level: 2, question: 'Why?', answer: 'Because B' }
    ]);
    
    const md = builder.toMarkdown();
    expect(md).toContain('**Q1**');
    expect(md).toContain('**A**: Because A');
  });
});
