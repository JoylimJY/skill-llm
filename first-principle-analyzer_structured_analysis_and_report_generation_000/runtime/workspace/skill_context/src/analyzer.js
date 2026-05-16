/**
 * first-principle-analyzer - 第一性原理分析器
 * 版本：v0.1.0
 * 
 * 核心功能：用第一性原理分解复杂问题，提取基本真理，重构创新方案
 * 
 * 灵感来源：
 * - Elon Musk 的第一性原理思维方法
 * - Linux Kernel 开发流程文档
 * - 亚里士多德物理学第一原理
 * - 笛卡尔方法论
 */

// ============================================================
// 配置与常量
// ============================================================

/**
 * 分析阶段定义
 */
const ANALYSIS_STAGES = {
  STAGE_1_PROBLEM_RECEIVE: 'stage_1_problem_receive',
  STAGE_2_ASSUMPTION_IDENTIFY: 'stage_2_assumption_identify',
  STAGE_3_ASSUMPTION_QUESTION: 'stage_3_assumption_question',
  STAGE_4_DECOMPOSITION: 'stage_4_decomposition',
  STAGE_5_TRUTH_VERIFY: 'stage_5_truth_verify',
  STAGE_6_RECONSTRUCT: 'stage_6_reconstruct',
  STAGE_7_REPORT_GENERATE: 'stage_7_report_generate'
};

/**
 * 问题类型分类
 */
const PROBLEM_TYPES = {
  TECHNICAL: 'technical',        // 技术架构
  BUSINESS: 'business',          // 商业决策
  PRODUCT: 'product',            // 产品方向
  LIFE: 'life',                  // 人生选择
  ACADEMIC: 'academic',          // 学术研究
  OTHER: 'other'                 // 其他
};

/**
 * 基本真理验证标准
 */
const TRUTH_VERIFICATION_CRITERIA = [
  '不可再分 - 无法进一步分解为更基本的组成部分',
  '不证自明 - 不需要其他命题证明其正确性',
  '独立性 - 不依赖于其他假设或命题',
  '普适性 - 在相关领域内普遍适用'
];

/**
 * 最小分解层数
 */
const MIN_DECOMPOSITION_LAYERS = 5;

// ============================================================
// 核心分析引擎
// ============================================================

/**
 * 第一阶段：问题接收与初步分析
 * @param {string} problem - 用户提出的问题
 * @returns {Object} 问题分析结果
 */
function stage1_problemReceive(problem) {
  console.log('[Stage 1] 接收问题:', problem);
  
  // 问题分类
  const problemType = classifyProblem(problem);
  console.log('[Stage 1] 问题分类:', problemType);
  
  // 初步假设识别
  const preliminaryAssumptions = identifyPreliminaryAssumptions(problem, problemType);
  console.log('[Stage 1] 初步假设:', preliminaryAssumptions);
  
  return {
    problem,
    problemType,
    preliminaryAssumptions,
    stage: ANALYSIS_STAGES.STAGE_1_PROBLEM_RECEIVE
  };
}

/**
 * 问题分类函数
 * @param {string} problem - 问题文本
 * @returns {string} 问题类型
 */
function classifyProblem(problem) {
  const keywords = {
    [PROBLEM_TYPES.TECHNICAL]: ['技术', '架构', '系统', '代码', '编程', '设计', '实现'],
    [PROBLEM_TYPES.BUSINESS]: ['商业', '市场', '投资', '公司', '盈利', '竞争', '战略'],
    [PROBLEM_TYPES.PRODUCT]: ['产品', '功能', '用户', '需求', '体验', '特性'],
    [PROBLEM_TYPES.LIFE]: ['人生', '工作', '生活', '选择', '职业', '家庭'],
    [PROBLEM_TYPES.ACADEMIC]: ['研究', '学术', '论文', '理论', '实验', '学科']
  };
  
  for (const [type, words] of Object.entries(keywords)) {
    if (words.some(word => problem.includes(word))) {
      return type;
    }
  }
  
  return PROBLEM_TYPES.OTHER;
}

/**
 * 初步假设识别
 * @param {string} problem - 问题文本
 * @param {string} problemType - 问题类型
 * @returns {Array<string>} 假设列表
 */
function identifyPreliminaryAssumptions(problem, problemType) {
  // 这是一个简化的实现，实际应该用 AI 模型进行深度分析
  const commonAssumptions = [
    '问题的当前表述方式是正确的',
    '问题的范围定义是合理的',
    '问题的约束条件是真实的'
  ];
  
  const typeSpecificAssumptions = {
    [PROBLEM_TYPES.TECHNICAL]: [
      '现有技术栈是必需的',
      '当前架构模式是最优的',
      '性能要求是合理的'
    ],
    [PROBLEM_TYPES.BUSINESS]: [
      '市场假设是准确的',
      '竞争格局是固定的',
      '商业模式是可行的'
    ],
    [PROBLEM_TYPES.PRODUCT]: [
      '用户需求是真实的',
      '功能优先级是正确的',
      '技术方案是合适的'
    ],
    [PROBLEM_TYPES.LIFE]: [
      '社会期望是合理的',
      '风险评估是准确的',
      '时间约束是真实的'
    ],
    [PROBLEM_TYPES.ACADEMIC]: [
      '研究范式是正确的',
      '理论基础是可靠的',
      '方法论是适当的'
    ]
  };
  
  return [
    ...commonAssumptions,
    ...(typeSpecificAssumptions[problemType] || [])
  ].slice(0, 5); // 返回最多 5 个假设
}

/**
 * 第二阶段：假设质疑
 * @param {Array<string>} assumptions - 假设列表
 * @returns {Array<Object>} 质疑结果
 */
function stage2_questionAssumptions(assumptions) {
  console.log('[Stage 2] 开始质疑假设');
  
  const questioningResults = assumptions.map((assumption, index) => {
    // 对每个假设进行质疑
    const questions = [
      `为什么这个假设一定成立？`,
      `这个假设的历史来源是什么？`,
      `有没有反例证明这个假设不成立？`,
      `如果这个假设不成立，会发生什么？`,
      `这个假设是物理必然还是人为约定？`
    ];
    
    return {
      assumption,
      index: index + 1,
      questions,
      status: 'pending' // pending / questioned / invalidated / confirmed
    };
  });
  
  console.log('[Stage 2] 质疑完成，结果:', questioningResults);
  
  return {
    questioningResults,
    stage: ANALYSIS_STAGES.STAGE_2_ASSUMPTION_IDENTIFY
  };
}

/**
 * 第三阶段：逐层分解（5 个为什么）
 * @param {string} problem - 原始问题
 * @param {number} layers - 分解层数（默认 5 层）
 * @returns {Array<Object>} 分解链
 */
function stage3_decompose(problem, layers = MIN_DECOMPOSITION_LAYERS) {
  console.log('[Stage 3] 开始逐层分解，层数:', layers);
  
  const decompositionChain = [];
  let currentQuestion = problem;
  
  for (let i = 0; i < layers; i++) {
    // 这是一个简化的实现，实际应该用 AI 模型生成深度追问
    const whyQuestion = `为什么${currentQuestion}？`;
    const answer = generateProvisionalAnswer(whyQuestion, i);
    
    decompositionChain.push({
      layer: i + 1,
      question: whyQuestion,
      answer,
      isBasicTruth: i === layers - 1 // 最后一层标记为基本真理候选
    });
    
    currentQuestion = answer;
  }
  
  console.log('[Stage 3] 分解完成，链长:', decompositionChain.length);
  
  return {
    decompositionChain,
    reachedLayers: layers,
    stage: ANALYSIS_STAGES.STAGE_3_DECOMPOSITION
  };
}

/**
 * 生成临时答案（简化实现）
 */
function generateProvisionalAnswer(question, layerIndex) {
  const answers = [
    '因为这是当前的技术/社会/经济约束条件下的结果',
    '因为历史发展路径依赖和既得利益结构',
    '因为信息不对称和认知局限',
    '因为资源稀缺性和分配机制',
    '这是基本真理层：物理规律/经济规律/人性本质'
  ];
  
  return answers[Math.min(layerIndex, answers.length - 1)];
}

/**
 * 第四阶段：基本真理验证
 * @param {Object} decompositionResult - 分解结果
 * @returns {Object} 验证结果
 */
function stage4_verifyTruth(decompositionResult) {
  console.log('[Stage 4] 开始验证基本真理');
  
  const basicTruthCandidate = decompositionResult.decompositionChain[
    decompositionResult.decompositionChain.length - 1
  ].answer;
  
  const verificationResults = TRUTH_VERIFICATION_CRITERIA.map((criterion, index) => {
    // 这是一个简化的实现，实际应该用 AI 模型进行评估
    const passed = index < 3; // 模拟：前 3 个标准通过
    
    return {
      criterion,
      passed,
      reasoning: passed ? '满足该标准' : '需要进一步验证'
    };
  });
  
  const allPassed = verificationResults.every(r => r.passed);
  
  console.log('[Stage 4] 验证完成，全部通过:', allPassed);
  
  return {
    basicTruthCandidate,
    verificationResults,
    allPassed,
    stage: ANALYSIS_STAGES.STAGE_4_TRUTH_VERIFY
  };
}

/**
 * 第五阶段：重构方案生成
 * @param {string} basicTruth - 基本真理
 * @param {string} originalProblem - 原始问题
 * @returns {Array<Object>} 重构方案列表
 */
function stage5_reconstruct(basicTruth, originalProblem) {
  console.log('[Stage 5] 开始从基本真理重构方案');
  
  // 这是一个简化的实现，实际应该用 AI 模型进行演绎推理
  const solutions = [
    {
      name: '方案 A：从基本真理演绎的最优解',
      description: '基于基本真理，重新设计解决方案，不考虑历史约束',
      innovation: '完全摆脱历史包袱，从零开始设计',
      feasibility: '中等 - 需要较大投入',
      risk: '中等 - 新技术/新模式的不确定性'
    },
    {
      name: '方案 B：渐进式重构',
      description: '在现有基础上，逐步应用基本真理进行改进',
      innovation: '平衡创新与可行性',
      feasibility: '高 - 可以利用现有资源',
      risk: '低 - 渐进式变革风险可控'
    },
    {
      name: '方案 C：颠覆式创新',
      description: '完全颠覆现有范式，创造全新解决方案',
      innovation: '最大化创新，可能创造新市场',
      feasibility: '低 - 需要突破性技术/资源',
      risk: '高 - 失败概率大，但成功回报也高'
    }
  ];
  
  console.log('[Stage 5] 重构完成，方案数:', solutions.length);
  
  return {
    solutions,
    basicTruth,
    stage: ANALYSIS_STAGES.STAGE_5_RECONSTRUCT
  };
}

/**
 * 第六阶段：类比方案对比
 * @param {Array<Object>} newSolutions - 新方案列表
 * @param {string} originalProblem - 原始问题
 * @returns {Object} 对比分析
 */
function stage6_compare(newSolutions, originalProblem) {
  console.log('[Stage 6] 开始对比分析');
  
  // 传统类比方案（基于行业惯例）
  const traditionalSolution = {
    name: '传统类比方案',
    description: '参考行业最佳实践和成功案例',
    basis: '类比思维：别人怎么做，我们就怎么做或稍作改进'
  };
  
  const comparison = {
    traditional: traditionalSolution,
    innovations: newSolutions.map((sol, index) => ({
      solution: sol.name,
      differences: [
        `从第一原理出发，而非类比`,
        `质疑了传统方案的隐含假设`,
        `方案${index + 1}的创新点：${sol.innovation}`
      ],
      advantages: [
        `更贴近问题本质`,
        `可能发现被忽视的机会`,
        `避免路径依赖`
      ]
    }))
  };
  
  console.log('[Stage 6] 对比完成');
  
  return {
    comparison,
    stage: ANALYSIS_STAGES.STAGE_6_RECONSTRUCT
  };
}

/**
 * 第七阶段：生成 Markdown 报告
 * @param {Object} analysisResult - 完整分析结果
 * @returns {string} Markdown 格式报告
 */
function stage7_generateReport(analysisResult) {
  console.log('[Stage 7] 开始生成报告');
  
  const report = `# 第一性原理分析报告

## 问题
${analysisResult.problem}

## 问题分类
${analysisResult.problemType}

---

## 识别的假设

${analysisResult.assumptions.questioningResults.map((r, i) => 
`${i + 1}. **${r.assumption}**`
).join('\n')}

---

## 假设质疑

${analysisResult.assumptions.questioningResults.map((r, i) => 
`### 假设 ${i + 1}: ${r.assumption}

**质疑问题**:
${r.questions.map(q => `- ${q}`).join('\n')}
`
).join('\n')}

---

## 分解到基本真理

${analysisResult.decomposition.decompositionChain.map((layer, i) => 
`**第${layer.layer}层**：
- 问题：${layer.question}
- 答案：${layer.answer}
${layer.isBasicTruth ? '- ✅ 基本真理候选' : ''}
`
).join('\n')}

---

## 基本真理验证

**基本真理候选**：${analysisResult.truthVerification.basicTruthCandidate}

**验证结果**：
${analysisResult.truthVerification.verificationResults.map(r => 
`- ${r.passed ? '✅' : '❌'} ${r.criterion}: ${r.reasoning}`
).join('\n')}

**结论**：${analysisResult.truthVerification.allPassed ? '✅ 通过验证' : '❌ 需要进一步验证'}

---

## 重构方案

${analysisResult.reconstruction.solutions.map((sol, i) => 
`### ${sol.name}

**描述**：${sol.description}

**创新点**：${sol.innovation}

**可行性**：${sol.feasibility}

**风险**：${sol.risk}
`
).join('\n')}

---

## 与类比方案对比

### 传统方案
${analysisResult.comparison.traditional.description}
*依据：${analysisResult.comparison.traditional.basis}*

### 创新方案优势

${analysisResult.comparison.innovations.map((comp, i) => 
`**${comp.solution}**:
${comp.differences.map(d => `- ${d}`).join('\n')}
${comp.advantages.map(a => `- ✅ ${a}`).join('\n')}
`
).join('\n')}

---

## 下一步建议

1. 选择最有前景的方案进行深入分析
2. 识别实施该方案的关键障碍
3. 制定具体的行动计划

---

**报告生成时间**：${new Date().toISOString()}
**分析引擎版本**：first-principle-analyzer v0.1.0
`;
  
  console.log('[Stage 7] 报告生成完成');
  
  return report;
}

// ============================================================
// 主分析流程
// ============================================================

/**
 * 执行完整的第一性原理分析
 * @param {string} problem - 用户问题
 * @returns {string} Markdown 格式分析报告
 */
function analyze(problem) {
  console.log('========================================');
  console.log('开始第一性原理分析');
  console.log('问题:', problem);
  console.log('========================================');
  
  // 阶段 1：问题接收
  const stage1Result = stage1_problemReceive(problem);
  
  // 阶段 2：假设质疑
  const stage2Result = stage2_questionAssumptions(stage1Result.preliminaryAssumptions);
  
  // 阶段 3：逐层分解
  const stage3Result = stage3_decompose(problem);
  
  // 阶段 4：基本真理验证
  const stage4Result = stage4_verifyTruth(stage3Result);
  
  // 阶段 5：重构方案
  const stage5Result = stage5_reconstruct(
    stage4Result.basicTruthCandidate,
    problem
  );
  
  // 阶段 6：对比分析
  const stage6Result = stage6_compare(stage5Result.solutions, problem);
  
  // 整合所有结果
  const fullResult = {
    problem,
    problemType: stage1Result.problemType,
    assumptions: stage2Result,
    decomposition: stage3Result,
    truthVerification: stage4Result,
    reconstruction: stage5Result,
    comparison: stage6Result
  };
  
  // 阶段 7：生成报告
  const report = stage7_generateReport(fullResult);
  
  console.log('========================================');
  console.log('分析完成');
  console.log('========================================');
  
  return report;
}

// ============================================================
// 导出接口
// ============================================================

module.exports = {
  analyze,
  ANALYSIS_STAGES,
  PROBLEM_TYPES,
  TRUTH_VERIFICATION_CRITERIA,
  MIN_DECOMPOSITION_LAYERS
};

// ============================================================
// 技能优化分析模式（新增）
// ============================================================

/**
 * 技能优化分析模式
 * 专门用于分析技能本身的改进方向
 * 
 * @param {string} skillName - 技能名称
 * @param {Object} currentVersion - 当前版本信息
 * @returns {Object} 优化分析报告
 */
function analyzeSkillOptimization(skillName, currentVersion) {
  console.log('[Skill Optimization] 开始分析技能:', skillName);
  
  // 分析框架
  const analysisFramework = {
    // 1. 当前状态分析
    currentStatus: {
      version: currentVersion.version,
      capabilities: currentVersion.capabilities || [],
      knownLimitations: currentVersion.knownLimitations || [],
      usageStats: currentVersion.usageStats || {}
    },
    
    // 2. 改进灵感搜集
    improvementSources: [
      '用户反馈',
      '使用数据分析',
      '专家模式库',
      '最新技术进展',
      '类似技能对比'
    ],
    
    // 3. 优化方向评估
    optimizationDimensions: [
      { name: '功能增强', weight: 0.3 },
      { name: '性能提升', weight: 0.2 },
      { name: '用户体验', weight: 0.2 },
      { name: '可维护性', weight: 0.15 },
      { name: '可扩展性', weight: 0.15 }
    ]
  };
  
  // 生成优化建议
  const optimizationSuggestions = generateOptimizationSuggestions(analysisFramework);
  
  // 生成优先级排序
  const prioritizedSuggestions = prioritizeSuggestions(optimizationSuggestions);
  
  return {
    skillName,
    currentVersion: currentVersion.version,
    analysisDate: new Date().toISOString(),
    framework: analysisFramework,
    suggestions: prioritizedSuggestions,
    nextVersionPlan: generateNextVersionPlan(prioritizedSuggestions)
  };
}

/**
 * 生成优化建议
 */
function generateOptimizationSuggestions(framework) {
  const suggestions = [];
  
  // 基于已知局限生成建议
  for (const limitation of framework.currentStatus.knownLimitations) {
    suggestions.push({
      type: 'limitation_fix',
      description: `解决局限：${limitation}`,
      dimension: '功能增强',
      priority: 'high',
      effort: 'medium',
      impact: 'high'
    });
  }
  
  // 基于能力缺口生成建议
  const expectedCapabilities = getExpectedCapabilities(framework.currentStatus.version);
  const missingCapabilities = expectedCapabilities.filter(
    cap => !framework.currentStatus.capabilities.includes(cap)
  );
  
  for (const capability of missingCapabilities) {
    suggestions.push({
      type: 'capability_add',
      description: `添加能力：${capability}`,
      dimension: '功能增强',
      priority: 'medium',
      effort: 'high',
      impact: 'high'
    });
  }
  
  // 基于使用数据生成建议
  if (framework.currentStatus.usageStats) {
    // 识别使用频率低的功能
    // 识别用户流失点
    // ...
  }
  
  return suggestions;
}

/**
 * 获取期望能力列表
 */
function getExpectedCapabilities(version) {
  // 根据版本号返回期望的能力
  // 这应该从知识库中获取
  return [];
}

/**
 * 优先级排序
 */
function prioritizeSuggestions(suggestions) {
  return suggestions.sort((a, b) => {
    const priorityOrder = { 'high': 3, 'medium': 2, 'low': 1 };
    const impactOrder = { 'high': 3, 'medium': 2, 'low': 1 };
    const effortOrder = { 'low': 3, 'medium': 2, 'high': 1 }; // 努力越小优先级越高
    
    const scoreA = priorityOrder[a.priority] * 0.4 + 
                   impactOrder[a.impact] * 0.4 + 
                   effortOrder[a.effort] * 0.2;
    
    const scoreB = priorityOrder[b.priority] * 0.4 + 
                   impactOrder[b.impact] * 0.4 + 
                   effortOrder[b.effort] * 0.2;
    
    return scoreB - scoreA;
  });
}

/**
 * 生成下一版本计划
 */
function generateNextVersionPlan(suggestions) {
  const topSuggestions = suggestions.slice(0, 5);
  
  return {
    targetVersion: 'v0.2.0',
    estimatedEffort: calculateTotalEffort(topSuggestions),
    estimatedImpact: calculateTotalImpact(topSuggestions),
    includedSuggestions: topSuggestions,
    timeline: {
      design: '1 week',
      implementation: '2 weeks',
      testing: '1 week',
      release: '1 week'
    }
  };
}

/**
 * 计算总努力
 */
function calculateTotalEffort(suggestions) {
  const effortMap = { 'low': 1, 'medium': 2, 'high': 3 };
  const total = suggestions.reduce((sum, s) => sum + effortMap[s.effort], 0);
  
  if (total <= 3) return 'low';
  if (total <= 6) return 'medium';
  return 'high';
}

/**
 * 计算总影响
 */
function calculateTotalImpact(suggestions) {
  const impactMap = { 'low': 1, 'medium': 2, 'high': 3 };
  const total = suggestions.reduce((sum, s) => sum + impactMap[s.impact], 0);
  
  if (total <= 3) return 'low';
  if (total <= 6) return 'medium';
  return 'high';
}

// 导出新函数
module.exports.analyzeSkillOptimization = analyzeSkillOptimization;
