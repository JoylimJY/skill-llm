# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.7] - 2026-03-19

### Fixed
- **update 命令返回 null** - 修复参数传递方式，从 `(id, data)` 改为 `{ id, ...data }` 对象
- **经验记录的 content 字段未正确保存** - 修复 `record_experience` 参数传递方式
- **verify_experience 测试失败** - 修复参数传递方式和测试代码中的字段读取路径
- CLI 测试代码中 verifiedCount 读取路径从顶层改为 `experienceMeta.verifiedCount`

---

## [1.3.6] - 2026-03-19

### Added
- CLI test suite (tests/cli.test.js)
- references/ directory with detailed documentation
- references/tools.md - detailed tool parameters
- references/examples.md - usage examples

### Changed
- SKILL.md 精简到 100 行以内
- Added license field to SKILL.md frontmatter
- Added references links to SKILL.md

---

## [1.3.5] - 2026-03-19

### Fixed
- CLI bug fixes for write, search, and experience management

---

## [1.2.1] - 2026-03-19

### Added
- Optimized vector model storage path - now supports dynamic skill directory
- Multi-language README support (EN, ZH, JA, ES)
- Improved model download path resolution

### Changed
- Vector model download path changed to skill directory for better integration
- Enhanced documentation with multi-language support

---

## [1.0.0] - 2026-03-18

### Added
- Initial release of Memory Palace
- Core memory management with CRUD operations
- Persistent file-based storage (Markdown format)
- Semantic search with vector search integration
- Text-based search fallback when vector search unavailable
- Time reasoning engine for temporal expressions (明天, 下周, 本月, etc.)
- Concept expansion for query enhancement
- Tagging system for flexible categorization
- Location-based memory organization
- Importance scoring for memory prioritization
- Soft delete with trash and restore functionality
- Background tasks support (conflict detection, memory compression)
- Knowledge graph builder for memory relationships
- Entity tracking and co-occurrence analysis
- Topic clustering for memory organization
- OpenClaw MemoryIndexManager integration support
- TypeScript type definitions
- Comprehensive test suite

### Technical Details
- No MCP protocol dependency - direct function calls
- Interface isolation - vector search is optional
- Graceful degradation - works without advanced features
- File-based storage - simple, portable, human-readable

---

## Future Plans

- [ ] Cloud sync support
- [ ] Memory encryption
- [ ] Advanced visualization
- [ ] Multi-agent memory sharing
- [ ] Natural language queries

---

🔥 Built with passion by the Chaos Team