# AI 系统提示词基本范式分析报告

## 一、数据集概况

| 维度 | 数量 |
|---|---|
| 覆盖工具/平台 | 37 个 |
| 提示词文件总数 | 81 个 |
| 严谨分析样本（结构化） | 21 个（XML × 10，Markdown × 11） |
| 补充验证样本 | 58 个（others，关键词 grep） |

**文件分类方法**：按文件首个非空字符判定格式（`<` → XML，`#` → Markdown，其余 → others）；在 XML/Markdown 内，以包含 `you are` 作为系统提示词标志，区分"系统提示词"与"不确定"。

---

## 二、分析方法

### Block 1 — 结构化提取（严谨）
- **XML**：提取所有 `<tag>` 名称，统计跨文件出现频率，再按语义归并
- **Markdown**：提取所有 `#/##/###` 标题，统计跨文件出现频率，再按语义归并
- 样本：xml/system-prompt（10 个）+ markdown/system-prompt（11 个）

### Block 2 — 关键词 grep（补充验证，精度有限）
- 对 58 个 others 文件，按每个模块的特征关键词进行正则扫描
- 结果仅作方向性参考，不用于修正 Block 1 结论

---

## 三、核心发现

### 3.1 格式层面：标签/标题名称高度离散

XML 标签中出现频率最高的 `<identity>` 仅覆盖 4/10 文件；Markdown 标题中出现频率最高的 `Identity` 仅覆盖 4/11 文件。各工具均自行发明标签/标题词汇，**不存在行业统一的命名规范**。

### 3.2 语义层面：模块高度收敛

将标签/标题按语义归并后，得到 **8 个跨格式、跨工具的语义模块**，在两种格式中均有对应，且 Block 2 数据方向一致，**未出现新模块**。

---

## 四、基本范式：8 个语义模块

### 覆盖率汇总

| 模块 | 层级 | XML（10） | Markdown（11） | Others grep（58） |
|---|---|---|---|---|
| **身份定义** | 核心 | 6/10 | 8/11 | 49/58，84% |
| **行为规范** | 核心 | 7/10 | 9/11 | 50/58，86% |
| **能力/工具** | 核心 | 5/10 | 7/11 | 46/58，79% |
| **输出格式** | 建议 | 5/10 | 5/11 | 32/58，55% |
| **示例** | 建议 | 3/10 | 4/11 | 51/58，88% |
| **约束/安全** | 建议 | 4/10 | 4/11 | 28/58，48% |
| **上下文/环境** | 按场景 | 3/10 | 5/11 | 32/58，55% |
| **任务管理** | 按场景 | 2/10 | 5/11 | 29/58，50% |

### 层级说明

- **核心**：几乎所有系统提示词都包含，缺失则提示词不完整
- **建议**：大多数提示词包含，对质量有明显影响
- **按场景**：在特定类型（如编码助手、Agent）中高频，通用对话场景中较少

---

## 五、模块描述

### 1. 身份定义（Identity Definition）
定义 AI 的角色、名称、定位。通常是提示词的第一句话。

典型写法：`You are [Name], a [role] that [goal].`

XML 代表标签：`<identity>` `<core_identity>` `<purpose>`
Markdown 代表标题：`# Identity` `# Role` `# Identity & Personality`

---

### 2. 行为规范（Behavioral Guidelines）
规定 AI 在交互中的一般行为准则，包括回复风格、主动性、谨慎程度等。

XML 代表标签：`<behavioral_rules>` `<guidelines>` `<communication_style>`
Markdown 代表标题：`# Rules` `# Communication Guidelines` `# Following instructions`

---

### 3. 能力/工具（Capabilities & Tools）
描述 AI 可使用哪些工具，以及工具调用的格式与规则。

XML 代表标签：`<tool_calling>` `<tool_list>` `<capabilities>` `<function_calls>`
Markdown 代表标题：`# Tool Calling Rules` `# Available Tools` `# Capabilities`

---

### 4. 输出格式（Output Format）
规定回复的结构、长度、语言风格、Markdown 使用等。

XML 代表标签：`<response_format>` `<response_formatting_instructions>` `<format_rules>`
Markdown 代表标题：`# RESPONSE FORMAT` `# Output formatting` `# Response style`

---

### 5. 示例（Examples）
通过具体案例示范正确/错误行为，增强指令的可操作性。

XML 代表标签：`<example>` `<good-example>` `<bad-example>`
Markdown 代表标题：`# Example` `# Usage Example`

---

### 6. 约束/安全（Constraints & Safety）
明确 AI 不应做的事，包括内容红线、安全规则、拒绝策略等。

XML 代表标签：`<restrictions>` `<forbidden_behaviors>` `<strict_prohibitions>` `<critical_security_rules>`
Markdown 代表标题：`# System Security - CRITICAL` `# Prohibited Content`

---

### 7. 上下文/环境（Context & Environment）
注入运行时信息：操作系统、工作目录、当前时间、用户信息等。

XML 代表标签：`<environment>` `<user_information>` `<persistent_context>`
Markdown 代表标题：`# System Information` `# ENVIRONMENT` `# Current date and time`

---

### 8. 任务管理（Task Management）
规范 AI 处理复杂任务的方式：分解步骤、追踪进度、主动性控制等。多见于编码 Agent。

XML 代表标签：`<task_management>` `<workflows>`
Markdown 代表标题：`# Task Management` `# Planning and Task Management` `# Proactiveness`

---

## 六、后续分析准备

第二步深入分析将针对结构化样本（21 个文件）的每个模块，提取并比较各工具的具体内容。

**检测配置文件**：`Analysis/module-detection-config.json`
包含每个模块的 XML 标签列表、Markdown 关键词、fallback 正则，供程序直接调用。

**分析目标**：
- 每个模块内部写了什么（内容规律）
- 同一模块在不同工具间的差异（横向对比）
- 是否存在子模式或变体

**文件范围**：
- `Analysis/format-classification/xml/system-prompt/`（10 个）
- `Analysis/format-classification/markdown/system-prompt/`（11 个）
