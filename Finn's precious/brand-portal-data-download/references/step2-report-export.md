# Step 2 - 报表导出与下载

## 2.1 导出前检查

- 确认报表名称。
- 确认国家、店铺、品牌、日期范围。
- 确认比较周期是否需要 previous period。
- 确认币种和时间粒度。

## 2.2 导出策略

优先顺序：
1. 官方下载按钮
2. 报表中心 / 下载中心
3. 页面网络请求或任务接口
4. 自动化浏览器截图辅助确认

## 2.3 下载后处理

- 保留原始文件名。
- 若文件名没有日期，补一层本地归档命名。
- 同一份报表如果有 current 和 previous，分别保存，不合并成一份假文件。

## 2.4 不同报表的常见口径

- `Sales Dashboard`：店铺经营结果，常见字段有 Sales、Orders、Unique Visitors、Product Views、Product Clicks。
- `Off-platform`：站外归因结果，常见字段有 Visits、Orders、GMV。
- `Product Performance`：商品层结果，按 Product ID 或商品维度汇总。
- `Traffic / Landing Rate`：看点击到入站的链路，不等于店铺转化。

