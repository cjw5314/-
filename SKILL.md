---
name: greenwashing-analysis-workflow
description: When user wants to reproduce the greenwashing detection process for listed companies, step by step guide.
---

## 【步骤1：制定爬取规格】

1. 打开文本编辑器（如Notepad++、VS Code）
2. 创建新文件，命名为 `crawl_spec.md`
3. 在文件中写入以下内容：
   ```
   # 爬取规格说明
   
   ## 数据范围
   - 股票池：50家上市公司（参考 heavy_50.txt）
   - 时间范围：2013-2024年（共12年）
   - 报告类型：年报、ESG报告、社会责任报告
   
   ## 搜索关键词
   - 年度报告
   - ESG报告
   - 社会责任报告
   - 环境报告书
   
   ## 爬虫配置
   - 限速策略：每请求间隔3-8秒
   - 线程数：单线程
   - 日请求上限：≤3000次
   ```
4. 保存文件到项目根目录

---

## 【步骤2：数据采集与元数据构建】

### 2.1 运行爬虫脚本
1. 打开命令行终端（CMD或PowerShell）
2. 切换到项目目录：
   ```bash
   cd D:\HuaweiMoveData\Users\Coco\Desktop\巨潮网作业
   ```
3. 运行爬虫脚本：
   ```bash
   python crawl_env_reports_v2.py
   ```
4. 等待脚本执行完成（可能需要较长时间）

### 2.2 查看输出结果
1. **PDF文件**：保存在 `downloads/{股票代码}_{公司名}/pdf/*.pdf`
2. **TXT文件**：保存在 `downloads/{股票代码}_{公司名}/txt/*.txt`（PDF转换后的文本）
3. **元数据文件**：生成 `metadata.csv`、`metadata_final.csv`、`metadata_final_v2.csv`

### 2.3 搜索环保处罚信息（手动补充）
1. 打开浏览器访问：http://www.cninfo.com.cn/new/disclosure/stock
2. 在搜索框输入股票代码（如 600019）
3. 选择对应公司后，进入公司公告页面
4. 在页面顶部点击"公告检索"或"历史公告"
5. 输入关键词："环境处罚" 或 "环保处罚"
6. 选择时间范围，点击搜索
7. 找到对应公告后，点击"查看PDF"或"下载"
8. 将处罚信息记录到 `处罚记录.csv`

---

## 【步骤3：建立环保字典】

### 3.1 提取核心词汇
1. 从已下载的年报TXT文件中提取环保相关词汇
2. 使用Python脚本统计高频词汇：
   ```bash
   python build_env_corpus_v2.py
   ```

### 3.2 词向量扩展
1. 使用腾讯词向量模型扩展相似词
2. 参考文档：`环保词汇词向量扩展方法.md`

### 3.3 人工筛选与分类
1. 打开生成的词汇表文件
2. 人工筛选去除无关词汇
3. 分类整理为4个词库：
   - `环保字典(1).csv` - 环境关键词基础库（62个词）
   - `模糊词汇扩展表——人工标注(1).csv` - 模糊表述识别（77个词）
   - `正面词汇扩展表——人工标注(1).xls` - 正面宣传强度（24个词）
   - `新证据词汇扩展表——人工标注.csv` - 证据密度计算（55个词）

---

## 【步骤4：字典可行度监测】

### 4.1 准备标注数据
1. 运行脚本提取环境相关句子：
   ```bash
   python extract_env_sentences.py
   ```
2. 输出文件：`环境句子抽取_基于报告词汇.csv`

### 4.2 人工标注
1. 打开Excel文件 `16家环境句子抽取.xlsx`
2. 对200句句子进行人工标注，每个句子标注3个维度：
   - **vague**：表述是否模糊（1=是，0=否）
   - **quant**：是否有数字量化（1=是，0=否）
   - **positive_no_evidence**：是否正面宣传但无证据（1=是，0=否）

### 4.3 一致性分析
1. 运行一致性分析脚本：
   ```bash
   python process_xlsx_and_analyze.py
   ```
2. 查看报告：`16家环境句子抽取_一致性分析报告.md`
3. 一致性要求：Cohen's Kappa ≥ 0.6（如不满足需重新调整字典）

---

## 【步骤5：计算漂绿指标】

### 5.1 运行计算脚本
1. 打开命令行终端
2. 运行最终版脚本：
   ```bash
   python calculate_greenwashing_components_v7.py
   ```

### 5.2 6个指标详细计算说明
1. **env_density（环境关键词密度）**：
   - 读取整个TXT文本
   - 统计环保关键词列表中所有词在文本中出现的总次数
   - 计算文本总字符数（含标点、空格、汉字、数字）
   - 公式：(总出现次数 ÷ 总字符数) × 1000

2. **vague_sent_ratio（模糊表述比例）**：
   - 将文本按句号、问号、感叹号、分号、换行分割成句子
   - 对每个句子，判断是否包含任意一个模糊词汇
   - 统计包含模糊词的句子数
   - 公式：模糊句子数 ÷ 总句子数

3. **quant_sent_ratio（量化披露比例）**：
   - 使用正则表达式匹配句子中是否有数字+常用环境单位
   - 正则：\d+(?:\.\d+)?\s*(?:[万亿千百]?吨|万千瓦时|%|万元|亿|千克|立方米|次|个|项|套|人|天|年)
   - 统计满足条件的句子数
   - 公式：量化句子数 ÷ 总句子数

4. **has_investment（环保投入披露）**：
   - 在全文中搜索模式：(环保投入|环境投资|环保支出|环保资金|环境治理投入)[^\d]*(\d+(?:\.\d+)?)\s*(?:万|亿)?元?
   - 如果匹配到至少一处 → has_investment = 1，否则 = 0

5. **positive_intensity（正面宣传强度）**：
   - 统计正面词汇列表中所有词在文本中出现的总次数
   - 公式：(总出现次数 ÷ 总字符数) × 1000

6. **evidence_per_page（证据密度）**：
   - 统计证据词汇列表中所有词在文本中出现的总次数
   - 估算页数：总字符数 ÷ 500
   - 公式：证据词次数 ÷ 页数

### 5.3 查看输出结果
1. 输出文件：`greenwashing_components_my.csv`
2. 文件包含字段：公司、年份、报告类型、6个指标值、总字符数、总句子数

---

## 【步骤6：建立模型与ESG对比】

### 6.1 计算综合指标
1. **positive_gap**：ESG报告正面密度 - 年报正面密度
2. **vague_gap**：ESG报告模糊密度 - 年报模糊密度
3. **has_penalty**：该年前后2年内是否有环保处罚记录（1=有，0=无）
4. **greenwash_alert**：positive_gap > 0.2 且 vague_gap > 0.2 且 has_penalty = 1

### 6.2 ESG评分对比分析
1. 获取第三方ESG评分数据（如华证ESG、商道融绿、Wind ESG）
2. 收集50家公司的ESG评分
3. 对比分析：
   - **潜在漂绿**：高ESG评分 + 高漂绿风险
   - **一致**：低ESG评分 + 低漂绿风险
   - **真实环保表现**：高ESG评分 + 低漂绿风险

---

## 【快速复现命令】

```bash
# 1. 环境准备
pip install pandas requests xlrd numpy

# 2. 数据采集（已有数据可跳过）
python crawl_env_reports_v2.py

# 3. 计算漂绿指标
python calculate_greenwashing_components_v7.py

# 4. 查看结果
cat greenwashing_components_my.csv
```

---

## 【项目文件结构】

```
巨潮网作业/
├── crawl_spec.md                    # 爬取规格说明书
├── URL获取指南.txt                   # URL获取指南
├── 处罚记录.csv                      # 环保处罚记录
├── metadata.csv                     # 元数据文件
├── metadata_final.csv               # 最终元数据版本1
├── metadata_final_v2.csv            # 最终元数据版本2
├── heavy_50.txt                     # 50家公司股票代码
├── crawl_env_reports.py             # 爬虫脚本v1
├── crawl_env_reports_v2.py          # 爬虫脚本v2
├── env_reports_found.csv            # 找到的环境报告列表
├── build_env_corpus_v2.py           # 环保语料库构建脚本
├── calculate_greenwashing_components_v7.py  # 漂绿指标计算（最终版）
├── greenwashing_components_my.csv   # 漂绿指标计算结果
├── downloads/                       # 下载的报告文件
│   ├── {股票代码}_{公司名}/
│   │   ├── pdf/*.pdf                # PDF原件
│   │   └── txt/*.txt                # TXT文本
└── .claude/
    └── skills/
        └── greenwashing-analysis-workflow/
            └── SKILL.md             # Claude技能配置
```