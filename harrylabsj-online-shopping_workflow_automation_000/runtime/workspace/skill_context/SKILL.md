---
name: harrylabsj-online-shopping
description: 全球电商平台智能推荐助手 - 基于商品类别、价格预算和物流需求，为用户推荐最适合的国际购物平台（Amazon、eBay、AliExpress、Temu等）。提供平台特性对比、购物时机建议和避坑指南。本Skill仅提供信息参考，不构成购买建议。
---

⚠️ **免责声明**：本Skill提供的平台推荐仅供参考，不构成购买建议。实际购物时请自行核实平台信息、卖家信誉和商品详情。我们不对任何购物决策承担责任。

# Online Shopping Guide

## Overview

本Skill帮助用户根据商品类别、预算和物流需求，智能推荐最适合的国际电商平台。

## Triggers

- "我想在亚马逊买东西"
- "哪个平台买...比较好"
- "推荐一个买...的网站"
- "Amazon 和 eBay 哪个好"
- "对比...平台"
- "全球购物推荐"
- "海淘推荐"
- "买...去哪个网站"

## Workflow

1. **识别用户购物需求**（商品类别、预算、时效要求等）
2. **调用 online-shopping.py** 获取平台推荐或对比
3. **呈现推荐结果**，包含推荐理由、最佳选择、注意事项
4. **如需详细指导**，引用 references/ 下的文档

## Usage

```bash
# 根据商品推荐平台
python3 online-shopping.py recommend <商品名称/类别>

# 列出支持的类别
python3 online-shopping.py categories

# 对比两个平台
python3 online-shopping.py compare <平台1> <平台2>
```

## Data Files

- `data/platforms.json` - 平台信息（特点、适用地区、优势类别）
- `data/categories.json` - 商品类别映射
- `data/regions.json` - 地区推荐配置

## References

- `references/platform-guide.md` - 平台详细指南
- `references/shopping-tips.md` - 购物技巧和注意事项

## Limitations

- 仅提供平台推荐信息，不进行实时价格查询
- 不访问任何购物平台的实时数据
- 推荐基于预设规则和静态数据
- 平台政策和费用可能随时变化，请以官方信息为准
