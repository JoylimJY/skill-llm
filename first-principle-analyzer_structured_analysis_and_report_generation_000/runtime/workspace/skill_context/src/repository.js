/**
 * Repository - 仓库模式实现
 * 
 * 封装分析历史的持久化存储逻辑
 * 灵感来源：meta-skill-weaver 状态持久化系统
 * 
 * 设计模式：仓库模式 (Repository Pattern)
 * - 抽象数据存储细节
 * - 提供统一的 CRUD 接口
 * - 支持多种存储后端（内存/文件/数据库）
 */

const fs = require('fs');
const path = require('path');

// ============================================================
// 存储接口定义
// ============================================================

/**
 * 存储后端接口
 * 定义仓库可使用的存储方式
 */
const STORAGE_BACKENDS = {
  MEMORY: 'memory',    // 内存存储（临时）
  FILE: 'file'         // 文件存储（持久）
};

/**
 * 分析记录结构
 */
class AnalysisRecord {
  constructor(data) {
    this.id = data.id || this._generateId();
    this.problem = data.problem;
    this.problemType = data.problemType;
    this.status = data.status || 'idle';
    this.result = data.result || null;
    this.report = data.report || null;
    this.stateSnapshot = data.stateSnapshot || null;
    this.createdAt = data.createdAt || new Date().toISOString();
    this.updatedAt = data.updatedAt || new Date().toISOString();
    this.metadata = data.metadata || {};
  }
  
  _generateId() {
    return `analysis_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  update(data) {
    Object.assign(this, data, { updatedAt: new Date().toISOString() });
    return this;
  }
  
  toJSON() {
    return { ...this };
  }
}

// ============================================================
// 内存存储后端
// ============================================================

class MemoryStorage {
  constructor() {
    this.store = new Map();
  }
  
  save(id, data) {
    this.store.set(id, data);
    return true;
  }
  
  findById(id) {
    return this.store.get(id) || null;
  }
  
  findAll(query = {}) {
    let records = Array.from(this.store.values());
    if (query.status) {
      records = records.filter(r => r.status === query.status);
    }
    if (query.problemType) {
      records = records.filter(r => r.problemType === query.problemType);
    }
    return records;
  }
  
  update(id, data) {
    if (!this.store.has(id)) return false;
    const record = this.store.get(id);
    Object.assign(record, data, { updatedAt: new Date().toISOString() });
    this.store.set(id, record);
    return true;
  }
  
  delete(id) {
    return this.store.delete(id);
  }
  
  count() {
    return this.store.size;
  }
}

// ============================================================
// 文件存储后端
// ============================================================

class FileStorage {
  constructor(basePath) {
    this.basePath = basePath;
    this._ensureDirectory();
  }
  
  _ensureDirectory() {
    if (!fs.existsSync(this.basePath)) {
      fs.mkdirSync(this.basePath, { recursive: true });
    }
  }
  
  _filePath(id) {
    return path.join(this.basePath, `${id}.json`);
  }
  
  save(id, data) {
    try {
      const filePath = this._filePath(id);
      fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
      return true;
    } catch (error) {
      console.error('[FileStorage] 保存失败:', error);
      return false;
    }
  }
  
  findById(id) {
    try {
      const filePath = this._filePath(id);
      if (!fs.existsSync(filePath)) return null;
      const content = fs.readFileSync(filePath, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      console.error('[FileStorage] 读取失败:', error);
      return null;
    }
  }
  
  findAll(query = {}) {
    try {
      const files = fs.readdirSync(this.basePath).filter(f => f.endsWith('.json'));
      let records = files.map(f => {
        const content = fs.readFileSync(path.join(this.basePath, f), 'utf8');
        return JSON.parse(content);
      });
      
      if (query.status) {
        records = records.filter(r => r.status === query.status);
      }
      if (query.problemType) {
        records = records.filter(r => r.problemType === query.problemType);
      }
      
      return records;
    } catch (error) {
      console.error('[FileStorage] 查询失败:', error);
      return [];
    }
  }
  
  update(id, data) {
    const existing = this.findById(id);
    if (!existing) return false;
    return this.save(id, { ...existing, ...data, updatedAt: new Date().toISOString() });
  }
  
  delete(id) {
    try {
      const filePath = this._filePath(id);
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
        return true;
      }
      return false;
    } catch (error) {
      console.error('[FileStorage] 删除失败:', error);
      return false;
    }
  }
  
  count() {
    try {
      const files = fs.readdirSync(this.basePath).filter(f => f.endsWith('.json'));
      return files.length;
    } catch (error) {
      return 0;
    }
  }
}

// ============================================================
// 仓库类
// ============================================================

class AnalysisRepository {
  /**
   * 创建仓库
   * @param {string} backend - 存储后端类型 ('memory' | 'file')
   * @param {Object} options - 配置选项
   */
  constructor(backend = STORAGE_BACKENDS.MEMORY, options = {}) {
    this.backend = backend;
    
    if (backend === STORAGE_BACKENDS.MEMORY) {
      this.storage = new MemoryStorage();
    } else if (backend === STORAGE_BACKENDS.FILE) {
      const basePath = options.basePath || path.join(__dirname, '../data/analyses');
      this.storage = new FileStorage(basePath);
    } else {
      throw new Error(`未知的存储后端：${backend}`);
    }
    
    console.log(`[Repository] 初始化仓库，后端：${backend}`);
  }
  
  /**
   * 创建分析记录
   * @param {Object} data - 分析数据
   * @returns {AnalysisRecord} 创建的分析记录
   */
  create(data) {
    const record = new AnalysisRecord(data);
    this.storage.save(record.id, record.toJSON());
    console.log(`[Repository] 创建分析记录：${record.id}`);
    return record;
  }
  
  /**
   * 查找分析记录
   * @param {string} id - 分析 ID
   * @returns {AnalysisRecord|null} 分析记录
   */
  findById(id) {
    const data = this.storage.findById(id);
    return data ? new AnalysisRecord(data) : null;
  }
  
  /**
   * 查询分析记录
   * @param {Object} query - 查询条件
   * @returns {Array<AnalysisRecord>} 分析记录列表
   */
  findAll(query = {}) {
    const records = this.storage.findAll(query);
    return records.map(r => new AnalysisRecord(r));
  }
  
  /**
   * 更新分析记录
   * @param {string} id - 分析 ID
   * @param {Object} data - 更新数据
   * @returns {boolean} 是否成功
   */
  update(id, data) {
    const success = this.storage.update(id, data);
    if (success) {
      console.log(`[Repository] 更新分析记录：${id}`);
    }
    return success;
  }
  
  /**
   * 删除分析记录
   * @param {string} id - 分析 ID
   * @returns {boolean} 是否成功
   */
  delete(id) {
    const success = this.storage.delete(id);
    if (success) {
      console.log(`[Repository] 删除分析记录：${id}`);
    }
    return success;
  }
  
  /**
   * 获取分析记录总数
   * @returns {number} 记录总数
   */
  count() {
    return this.storage.count();
  }
  
  /**
   * 获取最近的分析记录
   * @param {number} limit - 数量限制
   * @returns {Array<AnalysisRecord>} 分析记录列表
   */
  findRecent(limit = 10) {
    const all = this.findAll();
    return all
      .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
      .slice(0, limit);
  }
  
  /**
   * 获取统计信息
   * @returns {Object} 统计信息
   */
  getStats() {
    const all = this.findAll();
    const byStatus = {};
    const byProblemType = {};
    
    all.forEach(r => {
      byStatus[r.status] = (byStatus[r.status] || 0) + 1;
      byProblemType[r.problemType] = (byProblemType[r.problemType] || 0) + 1;
    });
    
    return {
      total: all.length,
      byStatus,
      byProblemType,
      completedRate: all.length > 0 ? (byStatus['completed'] || 0) / all.length : 0
    };
  }
}

module.exports = {
  STORAGE_BACKENDS,
  AnalysisRecord,
  MemoryStorage,
  FileStorage,
  AnalysisRepository
};
