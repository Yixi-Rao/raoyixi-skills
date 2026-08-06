---
name: survey-literature-closure
description: 执行基于原文证据、可恢复且可审计的系统文献调研：冻结题材范围与截止日期，递归遍历 references 和 cited-by，合并 arXiv/DOI/Semantic Scholar/OpenAlex 身份，判定核心/邻接/排除/待定论文，抽取并规范化 benchmark、基模型、训练框架或其他字段，证明来源有界的图固定点，并安全地暂存或写回表格/文档。用于 deep research、related work、系统综述、引用树/引用图递归、尽可能全面找论文、论文 codebase 或评测字段统计，以及任何要求可复现证据链而非一次搜索的调研。
---

# 文献闭包调研

## 先选择调研模式

根据用户要求选择且明确记录一种模式：

- **有限清单审计**：逐篇核验给定论文，不扩展引用图；只能声称清单内处理完成。
- **相关子图闭包**：从种子出发双向遍历 references 与 cited-by，直到来源有界的固定点；适用于“递归”“完整找全”“继续从引用查”等要求。
- **快速景观扫描**：按时间或关键词抽样；必须标注检索式、来源和覆盖限制，不得声称闭包或穷尽。

用户要求递归或尽可能完整时，默认采用相关子图闭包。不要用深度上限或“连续若干层没有新核心论文”冒充正常终止。

## 冻结范围契约

在抓取前完整阅读 [scope-and-taxonomy.md](references/scope-and-taxonomy.md)，然后冻结：

1. 研究问题与截止日期。
2. 可由原文证据判定的严格纳入条件。
3. 邻接条件、明确排除条件和待定处理规则。
4. 种子来源与种子清单。
5. 要抽取的字段、规范化粒度和输出目标。
6. 图来源、原文来源、预算及失败政策。

不要只写“与题材相关”。把核心条件拆成可逐项回答 `true/false/unknown` 的谓词。只有全部必要谓词为 `true` 才判为 `core`。

## 初始化可恢复项目

对多论文、递归或会跨回合运行的任务，创建持久化项目：

```bash
python3 scripts/scaffold_survey.py \
  --output /absolute/path/to/survey \
  --topic "目标题材" \
  --research-question "要回答的具体问题" \
  --cutoff YYYY-MM-DD \
  --include "严格纳入谓词 1" \
  --include "严格纳入谓词 2" \
  --exclude "明确排除谓词" \
  --adjacent-rule "与主题机制相邻且可能继续发现核心论文" \
  --seed "expert|arxiv:2401.01234" \
  --seed "keyword_search|title:另一篇候选论文" \
  --field "benchmark=论文实际用于正式评估并报告结果的公开 benchmark"
```

只在全新输出目录运行；脚本拒绝覆盖。将生成的范围契约、种子清单、SQLite 台账、判读模板、字段词表、stage-only mutation plan 和初始审计作为事实源，不以聊天上下文代替持久化状态。默认要求至少两类种子 provenance；若研究设计确实只允许一类，在契约中显式降低门槛并说明理由。

## 执行原文判读与字段抽取

在逐篇工作前完整阅读 [evidence-and-fields.md](references/evidence-and-fields.md)。遵守以下顺序：

1. 先规范化身份，再判断论文。
2. 优先打开官方 arXiv HTML；HTML 不可用时读取完整 PDF；非 arXiv 工作使用可验证的作者稿或出版社完整正文。
3. 至少检查摘要、方法、实验/评估、结果、限制和结论。
4. 对每个分类谓词和每个抽取字段记录原文位置、证据摘述、来源 URL 和证据等级。
5. 对未披露字段明确记录“论文未披露”，不要从作者代码、同系列论文或模型名称猜测。
6. 先建立规范化词表，再统计频率或写入多选字段；保留真正不同的版本、split 和配置。

在脚手架中把字段写成 `名称=操作性定义`；不要先创建空字段名，再让不同判读者自行解释。

仅摘要、搜索片段、引用标题或已有笔记不足以支持论文级分类和字段事实。无法取得完整原文或身份冲突时判为 `unresolved`，不要强行排除。

## 运行双向闭包

在实现或操作队列前完整阅读 [closure-and-delivery.md](references/closure-and-delivery.md)。保持以下状态机：

- `core`：满足全部严格条件；继续扩展。
- `adjacent`：不满足全部核心条件，但机制相邻并可能导向核心；继续扩展。
- `unresolved`：原文、身份或判定证据不足；继续扩展并阻止成功。
- `excluded`：原文证据足以确认范围外；作为叶子，不继续扩展。

对每个可扩展节点：

1. 从原文参考文献、Semantic Scholar 和 OpenAlex 取并集。
2. 抓完 references 与 cited-by 的全部分页。
3. 按 arXiv ID、DOI、索引 ID 和规范化标题合并身份；强 ID 冲突不得按标题静默合并。
4. 将新 ID 去重后加入筛选队列。
5. 每完成一个节点或分页便原子保存节点、边、游标、尝试次数和发现路径。

Crossref 只用于 DOI 和身份补全，不把其摘要当作完整原文。429/5xx 使用有界重试、持久化退避和来源切换；失败不能伪装成空结果。

## 使用并行代理但保持统一判尺

将独立论文或小批次分给子代理，并只提供范围契约、原文和标准化输出格式。要求每个子代理返回判定谓词、证据位置、身份、字段和不确定项。由主代理统一：

- 合并身份和词表；
- 复核全部核心候选与边界案例；
- 抽查排除节点；
- 处理代理间冲突；
- 控制队列和最终完成声明。

不要让不同代理自行创造 benchmark、模型系列、分类或证据等级口径。

## 验证固定点

每轮报告后运行：

```bash
python3 scripts/validate_closure.py \
  --contract /absolute/path/to/survey/survey_contract.json \
  --seed-manifest /absolute/path/to/survey/seed_manifest.json \
  --audit /absolute/path/to/survey/reports/closure_audit.json
```

完整字段定义见 [audit-contract.md](references/audit-contract.md)。只有验证器退出码为 `0` 才能宣布来源有界闭包成功。节点或墙钟保险触发时，报告“未完成/需要扩大预算”，不得当作正常停止。

## 暂存、写回与验收

任何外部写入前：

1. 先生成只读结果、证据表、规范化词表和 mutation plan。
2. 重新读取目标表/文档的实时 schema、视图、记录和全部多选项。
3. 优先使用 create-only 或 append-only；保护用户未授权字段。
4. 在图固定点前保持 stage-only，除非用户明确要求接受非闭包的中间结果。
5. 正式写入后完整回读，检查缺失、重复、字段不一致和受保护字段变化均为零。

处理飞书 Base 时调用 `lark-base`；处理飞书文档时调用 `lark-doc`，并遵循 [closure-and-delivery.md](references/closure-and-delivery.md) 的写回验收。API 成功、dry-run 或本地计划不等于真实写入完成。

## 报告状态

始终区分：

- **流程已实现**：工具和门禁可用。
- **本轮已处理**：给出节点、队列、失败和证据计数。
- **闭包已完成**：所有成功门同时通过。
- **外部结果已写入**：有正式 mutation 和实时回读证据。

完成声明必须限定截止日期、实际使用的原文与索引来源以及“相关子图”。明确说明它不覆盖任何来源均未收录的论文。
