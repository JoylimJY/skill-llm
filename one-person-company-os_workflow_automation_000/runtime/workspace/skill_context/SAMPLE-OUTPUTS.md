# Sample Outputs

These excerpts show the current behavior: language-aware company setup, current-round control, calibration, and stage transition.

## 交互输出结构

中文用户看到中文版本，英文用户看到英文版本；下面保留的是中文示例。

Every major operation now includes:

- `用户导航版`
  - 三层导航条
  - 本次会做 / 不会做
  - 本次变化
  - 回合仪表盘
  - 查看与改进
  - 保存解释
  - 运行解释
- `审计版`
  - 状态栏
  - 保存状态
  - 运行状态

## 公司总览

From `assets/examples/zh-round-mode/00-公司总览.md`

```md
- 产品名称: 北辰助手
- 当前阶段: 构建期
- 当前主目标: 完成首个可外测版本
- 当前瓶颈: 首页价值主张与注册入口还未收敛
- 当前回合: 完成首页首屏
```

这里的“当前阶段”应理解为主瓶颈标签，而不是重型流程阶段。

## 当前回合

From `assets/examples/zh-round-mode/01-当前回合.md`

```md
- 当前状态: 执行中
- 负责角色: 产品负责人
- 回合目标: 完成首页首屏结构与注册入口
- 当前阻塞: 首屏信息层级仍不稳定
- 下一步最短动作: 重写首屏主标题与副标题
```

## 校准记录

From `assets/examples/zh-round-mode/02-校准记录.md`

```md
- 触发原因: 30 分钟内无法确定首屏价值主张
- 当前结论: 需要产品负责人先收敛目标用户表达
- 下一步最短动作: 把目标用户缩小到做 AI SaaS 的独立开发者
```

## 示例工作区

```text
北辰实验室/
  00-公司总览.md
  01-产品定位.md
  02-当前阶段.md
  03-组织架构.md
  04-当前回合.md
  05-推进规则.md
  06-触发器与校准规则.md
  07-交付物地图.md
  08-阶段角色与交付矩阵.md
  09-当前阶段交付要求.md
  10-创始人启动卡.md
  11-交付目录总览.md
  12-AI时代快循环.md
  角色智能体/
  流程/
  产物/01-实际交付/01-实际产出总表.docx
  产物/02-软件与代码/01-代码与功能交付清单.docx
  产物/03-非软件与业务/01-非软件交付清单.docx
  产物/04-部署与生产/01-部署与回滚清单.docx
  记录/
  自动化/
```
