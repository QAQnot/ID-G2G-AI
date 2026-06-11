---
name: brand-portal-data-download
description: Shopee Brand Portal 数据下载工作流。触发词：Brand Portal 下载、BP 数据下载、导出 BP 报表、下载 Brand Portal 报表、导出 Sales Dashboard、导出 Off-platform 数据、下载 Shop Dashboard。
argument-hint: "report_type[可选：Sales Dashboard/Off-platform/Product Performance/Traffic/Download Center] date_range[可选：YYYY-MM-DD 到 YYYY-MM-DD] output_dir[可选：保存目录]"
metadata:
  version: "1.0.0"
  updated: "2026-05-28"
  tags: "brand-portal,download,shopee,report-export"
---

⚠️ 开始前确认以下 3 项，缺少任一项先向用户确认：
- [ ] 目标报表类型或页面入口
- [ ] 日期范围
- [ ] 保存位置或是否复用现有下载目录

---

先读取以下参考文件，再开始下载：
- Step 1 登录与入口定位：[step1-login-and-entry.md](references/step1-login-and-entry.md)
- Step 2 报表导出与下载：[step2-report-export.md](references/step2-report-export.md)
- Step 3 文件校验与命名：[step3-file-validation.md](references/step3-file-validation.md)
- 输出规范：[output-structure.md](references/output-structure.md)

---

## 产出物
- 下载完成的原始报表文件，通常是 `.xlsx` 或 `.csv`
- 下载日志或导出结果清单
- 如用户要求，可补一份简短的下载摘要

---

## 禁止项
- 不要编造下载成功或文件名
- 不要把旧日期文件冒充成新日期文件
- 不要静默覆盖用户未确认的同名文件
- 不要把 Brand Portal 的页面截图或导出文件内容擅自改写成分析结论
- 不要把不同报表口径混在同一个下载结果里

---

## Changelog
### [1.0.0] - 2026-05-28
#### Added
- 初版 Brand Portal 数据下载 skill，拆分登录、导出、校验三个步骤。
