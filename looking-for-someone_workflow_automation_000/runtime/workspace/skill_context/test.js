const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { LookingForSomeone } = require('./scripts/index');

const dataDir = path.join(os.homedir(), '.openclaw', 'skills-data', 'looking-for-someone');

function cleanup() {
  const file = path.join(dataDir, 'cases.json');
  if (fs.existsSync(file)) fs.unlinkSync(file);
}

function run() {
  cleanup();

  const app = new LookingForSomeone();
  const created = app.createCase({
    name: '张三',
    age: 16,
    gender: '男',
    lastSeenDate: '2026-03-10',
    lastSeenLocation: '北京市朝阳区',
    phone: '13800000000',
    idNumber: '110101200001011234',
    height: 175,
    clothing: '黑色外套',
    distinguishingFeatures: ['戴眼镜'],
    circumstances: '与家人争吵后离开',
    possibleDestinations: ['朝阳公园'],
    familyContacts: [{ name: '李女士' }]
  });

  assert.equal(created.success, true, 'case should be created');
  assert.ok(created.caseId, 'case id should exist');
  assert.equal(created.caseData.basicInfo.idNumber.masked, '1101********1234', 'id should be masked');

  const list = app.getAllCases();
  assert.equal(list.length, 1, 'should have one case');

  const clue = app.addClue(created.caseId, {
    content: '有人在北京市朝阳区地铁站附近见过他',
    source: 'user',
    reliability: 'high',
    verified: false
  });
  assert.equal(clue.success, true, 'clue should be added');
  assert.ok(clue.analysis.actionItems.length > 0, 'clue analysis should exist');

  const poster = app.generatePoster(created.caseId, 'wechat');
  assert.equal(poster.success, true, 'poster should be generated');
  assert.ok(poster.content.includes('张三'), 'poster should include name');

  const progress = app.getProgress(created.caseId);
  assert.equal(progress.success, true, 'progress should load');
  assert.equal(progress.summary.totalClues, 1, 'should count clues');
  assert.equal(progress.riskAssessment.level, 'high', 'minor case should be high risk');

  const warnings = app.getScamWarnings();
  assert.ok(Array.isArray(warnings) && warnings.length > 0, 'warnings should exist');

  console.log('All tests passed for looking-for-someone skill.');
}

run();
