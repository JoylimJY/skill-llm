/**
 * Repository 测试
 */

const {
  STORAGE_BACKENDS,
  AnalysisRecord,
  MemoryStorage,
  AnalysisRepository
} = require('../src/repository');

describe('AnalysisRecord', () => {
  test('应该创建分析记录', () => {
    const record = new AnalysisRecord({
      problem: '如何降低云成本？',
      problemType: 'business'
    });
    
    expect(record.id).toBeDefined();
    expect(record.problem).toBe('如何降低云成本？');
    expect(record.problemType).toBe('business');
    expect(record.status).toBe('idle');
  });
  
  test('应该能够更新记录', () => {
    const record = new AnalysisRecord({ problem: '测试问题' });
    record.update({ status: 'completed', result: '成功' });
    
    expect(record.status).toBe('completed');
    expect(record.result).toBe('成功');
    expect(record.updatedAt).toBeDefined();
  });
});

describe('MemoryStorage', () => {
  let storage;
  
  beforeEach(() => {
    storage = new MemoryStorage();
  });
  
  test('应该保存和检索数据', () => {
    const data = { id: 'test-001', name: '测试' };
    storage.save('test-001', data);
    
    const retrieved = storage.findById('test-001');
    expect(retrieved).toEqual(data);
  });
  
  test('应该返回 null 对于不存在的 ID', () => {
    const result = storage.findById('non-existent');
    expect(result).toBeNull();
  });
  
  test('应该能够查询所有记录', () => {
    storage.save('1', { id: '1', status: 'completed' });
    storage.save('2', { id: '2', status: 'idle' });
    storage.save('3', { id: '3', status: 'completed' });
    
    const all = storage.findAll();
    expect(all.length).toBe(3);
    
    const completed = storage.findAll({ status: 'completed' });
    expect(completed.length).toBe(2);
  });
  
  test('应该能够更新记录', () => {
    storage.save('test-001', { id: 'test-001', status: 'idle' });
    storage.update('test-001', { status: 'completed' });
    
    const record = storage.findById('test-001');
    expect(record.status).toBe('completed');
  });
  
  test('应该能够删除记录', () => {
    storage.save('test-001', { id: 'test-001' });
    storage.delete('test-001');
    
    expect(storage.findById('test-001')).toBeNull();
  });
});

describe('AnalysisRepository', () => {
  let repo;
  
  beforeEach(() => {
    repo = new AnalysisRepository(STORAGE_BACKENDS.MEMORY);
  });
  
  test('应该创建分析记录', () => {
    const record = repo.create({
      problem: '如何改进产品？',
      problemType: 'product'
    });
    
    expect(record.id).toBeDefined();
    expect(repo.count()).toBe(1);
  });
  
  test('应该能够查找记录', () => {
    const created = repo.create({ problem: '测试问题' });
    const found = repo.findById(created.id);
    
    expect(found).not.toBeNull();
    expect(found.problem).toBe('测试问题');
  });
  
  test('应该能够查询记录列表', () => {
    repo.create({ problem: '问题 1', problemType: 'business' });
    repo.create({ problem: '问题 2', problemType: 'product' });
    
    const all = repo.findAll();
    expect(all.length).toBe(2);
    
    const business = repo.findAll({ problemType: 'business' });
    expect(business.length).toBe(1);
  });
  
  test('应该能够获取最近的记录', () => {
    repo.create({ problem: '问题 1' });
    repo.create({ problem: '问题 2' });
    repo.create({ problem: '问题 3' });
    
    const recent = repo.findRecent(2);
    expect(recent.length).toBe(2);
  });
  
  test('应该能够获取统计信息', () => {
    repo.create({ problem: '问题 1', status: 'completed' });
    repo.create({ problem: '问题 2', status: 'idle' });
    repo.create({ problem: '问题 3', status: 'completed' });
    
    const stats = repo.getStats();
    expect(stats.total).toBe(3);
    expect(stats.byStatus.completed).toBe(2);
    expect(stats.byStatus.idle).toBe(1);
    expect(stats.completedRate).toBeCloseTo(2/3, 2);
  });
});
