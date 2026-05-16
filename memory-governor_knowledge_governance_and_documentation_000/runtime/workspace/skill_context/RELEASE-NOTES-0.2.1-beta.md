# Memory Governor 0.2.1-beta

`memory-governor` 现在已经进入一个可以对外解释、可以被第三方接入、也可以被轻量 bootstrap 的 beta 形态。

这次发布的重点不是“加更多功能”，而是把它从内部可用的治理内核，补成一个更像 skill 包的产品形态。

## What Shipped

- 核心模型已经稳定为：
  `memory type -> target class -> adapter / fallback`
- OpenClaw 不再被写成默认世界观，而是 reference host profile
- optional skills 不再是隐藏前提，而是可选 adapter
- 包内已经自带 fallback 模板、集成模板、安装说明
- 已经有 generic host 示例目录
- 已经有 lightweight bootstrap 脚本
- 已经有 `memory-governor-host.toml` 这种声明式宿主 contract
- host checker 已支持 manifest-driven 检查

## Why This Matters

这意味着第三方接入者不需要：

- 先理解 OpenClaw 全部目录结构
- 安装 `self-improving` 或 `proactivity`
- 手抄一整套宿主骨架

他们可以先：

1. 阅读 `README.md`
2. 看 `examples/generic-host/`
3. 修改 `memory-governor-host.toml`
4. 运行 `scripts/bootstrap-generic-host.sh`
5. 再替换成自己的真实 skill 和路径

## Package Status

当前状态建议理解为：

- internal architecture: stable
- distributable skill package: beta
- public release polish: not finished

## Recommended Next Step

如果后面要继续产品化，优先级建议是：

1. 做更完整的公开发布包装
2. 再考虑 release automation
