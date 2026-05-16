const fs = require('fs');
const path = require('path');
const os = require('os');

class LookingForSomeone {
  constructor() {
    this.dataDir = path.join(os.homedir(), '.openclaw', 'skills-data', 'looking-for-someone');
    this.ensureDir();
    this.cases = this.loadCases();
  }

  ensureDir() {
    if (!fs.existsSync(this.dataDir)) {
      fs.mkdirSync(this.dataDir, { recursive: true });
    }
  }

  get casesFile() {
    return path.join(this.dataDir, 'cases.json');
  }

  loadCases() {
    if (!fs.existsSync(this.casesFile)) return {};
    return JSON.parse(fs.readFileSync(this.casesFile, 'utf-8'));
  }

  saveCases() {
    fs.writeFileSync(this.casesFile, JSON.stringify(this.cases, null, 2));
  }

  saveCase(caseData) {
    this.cases[caseData.id] = caseData;
    this.saveCases();
  }

  maskIdNumber(idNumber) {
    if (!idNumber) return null;
    const text = String(idNumber);
    if (text.length <= 8) return `${text.slice(0, 2)}****${text.slice(-2)}`;
    return `${text.slice(0, 4)}********${text.slice(-4)}`;
  }

  createCase(input) {
    if (!input?.name || !input?.age || !input?.gender || !input?.lastSeenDate || !input?.lastSeenLocation) {
      return { success: false, error: '缺少必要字段：name, age, gender, lastSeenDate, lastSeenLocation' };
    }

    const now = new Date().toISOString();
    const id = `case_${Date.now()}`;
    const caseData = {
      id,
      createdAt: now,
      updatedAt: now,
      status: 'active',
      basicInfo: {
        name: input.name,
        gender: input.gender,
        age: input.age,
        birthDate: input.birthDate,
        phone: input.phone,
        idNumber: input.idNumber ? { masked: this.maskIdNumber(input.idNumber) } : undefined
      },
      appearance: {
        height: input.height,
        build: input.build || '不详',
        hairStyle: input.hairStyle || '不详',
        clothing: input.clothing,
        distinguishingFeatures: input.distinguishingFeatures || []
      },
      missingInfo: {
        lastSeenDate: input.lastSeenDate,
        lastSeenLocation: input.lastSeenLocation,
        circumstances: input.circumstances,
        possibleDestinations: input.possibleDestinations || []
      },
      relationships: {
        family: input.familyContacts || []
      },
      clues: [],
      searchHistory: []
    };

    this.saveCase(caseData);
    return { success: true, caseId: id, caseData, message: '案件已创建' };
  }

  analyzeClue(caseData, clue) {
    const content = clue.content || '';
    const actionItems = [];
    let relevance = 'medium';
    if (content.includes(caseData.missingInfo.lastSeenLocation || '')) relevance = 'high';
    if (/监控|医院|派出所|救助站/.test(content)) actionItems.push('优先核实该线索并联系对应机构');
    if (/看到|见过|出现/.test(content)) actionItems.push('尽快确认时间、地点、目击者身份');
    if (actionItems.length === 0) actionItems.push('记录线索来源并进一步核验');
    return { relevance, actionItems };
  }

  addClue(caseId, clue) {
    const caseData = this.cases[caseId];
    if (!caseData) return { success: false, error: '案件不存在' };

    const record = {
      id: `clue_${Date.now()}`,
      type: clue.type || 'tip',
      content: clue.content,
      source: clue.source || 'unknown',
      reliability: clue.reliability || 'unknown',
      verified: Boolean(clue.verified),
      timestamp: clue.timestamp || new Date().toISOString(),
      addedAt: new Date().toISOString()
    };

    const analysis = this.analyzeClue(caseData, record);
    caseData.clues.push(record);
    caseData.updatedAt = new Date().toISOString();
    this.saveCase(caseData);

    return { success: true, message: '线索已添加', clue: record, analysis };
  }

  generatePoster(caseId, platform = 'general') {
    const caseData = this.cases[caseId];
    if (!caseData) {
      return { success: false, error: '案件不存在' };
    }

    const templates = {
      general: this.generateGeneralPoster(caseData),
      wechat: this.generateWechatPoster(caseData),
      weibo: this.generateWeiboPoster(caseData),
      douyin: this.generateDouyinPoster(caseData),
      official: this.generateOfficialPoster(caseData)
    };

    return {
      success: true,
      platform,
      content: templates[platform] || templates.general,
      tips: this.getPosterTips(platform)
    };
  }

  generateGeneralPoster(caseData) {
    const { basicInfo, appearance, missingInfo } = caseData;
    return `【寻人启事】\n\n姓名：${basicInfo.name}\n性别：${basicInfo.gender}\n年龄：${basicInfo.age}岁\n身高：${appearance.height || '不详'}cm\n体貌特征：${appearance.distinguishingFeatures.join('、') || '详见照片'}\n\n失联时间：${missingInfo.lastSeenDate}\n失联地点：${missingInfo.lastSeenLocation}\n\n失联时衣着：${appearance.clothing || '不详'}\n\n如有线索，请联系：${basicInfo.phone || '（请联系家属）'}\n\n恳请大家转发扩散，帮助寻找！\n\n#寻人 #紧急寻人`;
  }

  generateWechatPoster(caseData) {
    const { basicInfo, missingInfo } = caseData;
    return `【紧急寻人】\n\n${basicInfo.name}，${basicInfo.age}岁，${basicInfo.gender}\n\n${missingInfo.lastSeenDate}在${missingInfo.lastSeenLocation}失联\n\n${missingInfo.circumstances || '如有线索请联系'}\n\n请大家帮忙转发，谢谢！🙏`;
  }

  generateWeiboPoster(caseData) {
    const { basicInfo, appearance, missingInfo } = caseData;
    return `【寻人启事】\n\n姓名：${basicInfo.name}\n年龄：${basicInfo.age}岁\n身高：${appearance.height || '不详'}cm\n特征：${appearance.distinguishingFeatures.slice(0, 2).join('、') || '详见照片'}\n\n于${missingInfo.lastSeenDate}在${missingInfo.lastSeenLocation}失联\n\n恳请转发扩散！\n\n@本地公安 @本地媒体`;
  }

  generateDouyinPoster(caseData) {
    const { basicInfo, missingInfo } = caseData;
    return `紧急寻人！${basicInfo.name}，${basicInfo.age}岁\n${missingInfo.lastSeenDate}在${missingInfo.lastSeenLocation}失联\n\n请大家帮忙留意！\n\n#寻人 #紧急寻人 #${basicInfo.name}`;
  }

  generateOfficialPoster(caseData) {
    const { basicInfo, appearance, missingInfo, relationships } = caseData;
    return `寻人启事\n\n一、基本信息\n姓名：${basicInfo.name}\n性别：${basicInfo.gender}\n出生日期：${basicInfo.birthDate || '不详'}\n身份证号：${basicInfo.idNumber?.masked || '（隐私保护）'}\n\n二、体貌特征\n身高：${appearance.height || '不详'}cm\n体型：${appearance.build}\n发型：${appearance.hairStyle}\n特殊标记：${appearance.distinguishingFeatures.join('、') || '无'}\n\n三、失联情况\n失联时间：${missingInfo.lastSeenDate}\n失联地点：${missingInfo.lastSeenLocation}\n失联经过：${missingInfo.circumstances || '待补充'}\n\n四、联系方式\n家属联系人：${relationships.family[0]?.name || '（请联系警方）'}\n联系电话：${basicInfo.phone || '（请联系警方）'}\n\n五、备注\n${missingInfo.possibleDestinations.length > 0 ? '可能去向：' + missingInfo.possibleDestinations.join('、') : ''}\n\n如有线索，请立即联系家属或拨打110报警。`;
  }

  getPosterTips(platform) {
    const tips = {
      general: ['附上清晰照片', '留下有效联系方式', '定期更新信息'],
      wechat: ['朋友圈可见范围设为公开', '请好友帮忙转发', '加入本地群组扩散'],
      weibo: ['@相关账号增加曝光', '添加话题标签', '定时转发保持热度'],
      douyin: ['制作短视频效果更好', '使用热门音乐', '添加定位信息'],
      official: ['到派出所盖章确认', '保留原件备查', '定期更新进展']
    };
    return tips[platform] || tips.general;
  }

  getProgress(caseId) {
    const caseData = this.cases[caseId];
    if (!caseData) {
      return { success: false, error: '案件不存在' };
    }

    const daysSince = Math.floor((new Date() - new Date(caseData.createdAt)) / (1000 * 60 * 60 * 24));
    const verifiedClues = caseData.clues.filter(c => c.verified).length;
    const highReliabilityClues = caseData.clues.filter(c => c.reliability === 'high').length;

    return {
      success: true,
      caseId,
      status: caseData.status,
      daysSince,
      summary: {
        totalClues: caseData.clues.length,
        verifiedClues,
        highReliabilityClues,
        lastUpdate: caseData.updatedAt
      },
      recentClues: caseData.clues.slice(-5).reverse(),
      nextActions: this.suggestNextActions(caseData),
      riskAssessment: this.assessRisk(caseData)
    };
  }

  suggestNextActions(caseData) {
    const actions = [];
    const { clues, searchHistory } = caseData;
    if (clues.length === 0) actions.push('积极收集线索：联系亲友、查看监控');
    if (!searchHistory.some(s => s.channel === 'social')) actions.push('在社交媒体发布寻人信息');
    if (!searchHistory.some(s => s.channel === 'police')) actions.push('立即向派出所报案');

    const daysMissing = Math.floor((new Date() - new Date(caseData.missingInfo.lastSeenDate)) / (1000 * 60 * 60 * 24));
    if (daysMissing > 7) {
      actions.push('扩大搜索范围到周边城市');
      actions.push('联系专业寻人机构');
    }
    return actions;
  }

  assessRisk(caseData) {
    const { basicInfo, missingInfo, clues } = caseData;
    let riskLevel = 'medium';
    const factors = [];

    if (basicInfo.age < 18 || basicInfo.age > 65) {
      riskLevel = 'high';
      factors.push('高龄/低龄，自我保护能力弱');
    }

    const daysMissing = Math.floor((new Date() - new Date(missingInfo.lastSeenDate)) / (1000 * 60 * 60 * 24));
    if (daysMissing > 7) {
      riskLevel = 'high';
      factors.push('失联时间较长');
    } else if (daysMissing > 3) {
      factors.push('失联时间中等');
    }

    if (clues.length === 0) factors.push('无线索');
    if (missingInfo.circumstances?.includes('矛盾') || missingInfo.circumstances?.includes('争吵')) {
      factors.push('可能存在情绪问题');
    }

    return {
      level: riskLevel,
      factors,
      recommendation: riskLevel === 'high' ? '建议立即报警并扩大搜索范围' : '保持积极搜索，定期更新信息'
    };
  }

  getAllCases() {
    return Object.values(this.cases).map(c => ({
      id: c.id,
      name: c.basicInfo.name,
      status: c.status,
      age: c.basicInfo.age,
      lastSeenDate: c.missingInfo.lastSeenDate,
      lastSeenLocation: c.missingInfo.lastSeenLocation,
      createdAt: c.createdAt,
      daysSince: Math.floor((new Date() - new Date(c.createdAt)) / (1000 * 60 * 60 * 24))
    }));
  }

  updateStatus(caseId, status, note) {
    const caseData = this.cases[caseId];
    if (!caseData) return { success: false, error: '案件不存在' };

    caseData.status = status;
    caseData.updatedAt = new Date().toISOString();
    if (note) {
      caseData.clues.push({
        id: `clue_${Date.now()}`,
        type: 'status_update',
        content: note,
        timestamp: new Date().toISOString(),
        addedAt: new Date().toISOString()
      });
    }
    this.saveCase(caseData);
    return { success: true, message: `案件状态已更新为：${status}`, caseData };
  }

  getScamWarnings() {
    return [
      '⚠️ 警惕要求转账的"线索" - 任何要求先付款的都是诈骗',
      '⚠️ 核实对方身份 - 要求提供工作证或警方证明',
      '⚠️ 不要泄露敏感信息 - 身份证号、银行卡号等',
      '⚠️ 通过官方渠道核实 - 不要轻信陌生来电',
      '⚠️ 正规寻人机构不会收取高额预付费用',
      '⚠️ 网络捐款需谨慎 - 确认收款方真实性'
    ];
  }

  getSearchGuide() {
    return {
      immediate: {
        title: '立即行动（0-24小时）',
        items: [
          '向当地派出所报案，获取报案回执',
          '联系最后出现地点的监控管理方',
          '检查手机定位、消费记录',
          '联系亲友扩大搜索',
          '在社交媒体发布寻人信息'
        ]
      },
      shortTerm: {
        title: '短期行动（1-7天）',
        items: [
          '在专业寻人平台注册发布',
          '联系救助站、医院',
          '在失联地点张贴寻人启事',
          '查看银行/支付记录',
          '扩大搜索范围到周边区域'
        ]
      },
      longTerm: {
        title: '长期行动（7天以上）',
        items: [
          '定期更新寻人信息',
          '扩大搜索范围到周边城市',
          '考虑聘请专业寻人机构',
          '保持与警方的联系',
          '关注网络线索和相似案例'
        ]
      }
    };
  }
}

module.exports = { LookingForSomeone };
