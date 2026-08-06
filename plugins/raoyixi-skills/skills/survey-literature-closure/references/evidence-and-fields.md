# 原文证据、身份与字段抽取

## 1. 使用证据层级

按以下优先级取证：

1. 官方 arXiv HTML 完整正文；
2. 官方 arXiv PDF；
3. 作者或机构公开的完整报告/作者稿；
4. 出版社完整正文；
5. 索引元数据，仅用于发现和身份补全。

将 arXiv `/abs/ID` 或 `/pdf/ID` 优先改为 `/html/ID`。HTML 缺失或不完整时再转 PDF，并保存文件哈希和抽取方式。付费墙、摘要页、搜索片段和生成式摘要均不构成完整原文。

## 2. 建立逐篇证据图

每篇至少记录：

```json
{
  "identity": {"title": "", "arxiv": null, "doi": null, "s2": null, "openalex": null},
  "source": {"url": "", "kind": "arxiv_html", "sha256": ""},
  "classification": "core|adjacent|excluded|unresolved",
  "criteria": [{"name": "C1", "value": "true|false|unknown", "location": "§4.2", "evidence": ""}],
  "fields": [{"name": "benchmark", "value": "", "location": "Table 3", "evidence": ""}],
  "uncertainties": [],
  "reviewer": ""
}
```

保存定位信息而非长篇复制原文。引用短摘述用于核对，分析使用自己的表述。

## 3. 完整阅读最小面

至少检查：

- Abstract/Introduction：问题和主张；
- Method/System：实际机制、训练或推理发生位置；
- Experiments/Evaluation：数据集、benchmark、基线、配置和指标；
- Results/Ablation：实际报告了什么，而非只在相关工作中提到什么；
- Limitations/Conclusion：适用边界和未披露项。

关键词查找只用于定位，不能代替阅读相邻段落、表格标题、脚注和附录。

## 4. 规范化论文身份

优先使用强标识：arXiv ID、DOI、Semantic Scholar ID、OpenAlex Work ID。将标题规范化仅用于候选匹配：Unicode 归一化、大小写折叠、空白和常见标点折叠。

遵守以下边界：

- 相同 arXiv/DOI 可合并版本并保留全部 alias。
- 相同规范化标题但强 ID 冲突时不得静默合并。
- DOI、arXiv、会议版本和技术报告是否为同一工作，必须用作者、正文和版本关系证明。
- 合并后保留发现路径、旧标识和判定证据；不要丢失 provenance。

## 5. 提取与规范化字段

先用 `名称=操作性定义` 冻结字段语义，再读论文：

- **benchmark**：纳入论文实际报告结果或明确用于正式评估的公开 benchmark；排除训练数据、内部未命名套件、工作负载标签、案例研究和仅在 related work 中提到的名称。
- **基模型系列**：按用户指定粒度归并参数规模；例如同系列不同参数可合并，但不同代际或专用变体是否合并必须写进词表。
- **训练框架**：仅记录原文或官方代码明确披露的框架；优化器、推理引擎和普通库不自动等同训练框架。
- **代码库**：区分官方仓库、第三方复现、仅项目主页和未公开。只有论文、官方项目页或作者/机构主页明确链接的仓库才标为官方。

未披露时使用统一缺失值，如“论文未披露”，不要猜测。

## 6. 维护规范化词表

为每个枚举或多选字段维护：

- canonical name；
- aliases；
- 版本与 split 边界；
- 合并理由和原文证据；
- 目标系统中已有选项 ID。

先比对 Unicode、空白、大小写、连字符、标点和显式 alias，再创建新选项。不要把 `v1/v2`、`test/dev` 或不同语言 split 仅因名称相似而合并。

## 7. 复核策略

要求所有核心候选由主代理或第二判读者复核。对邻接与排除节点按风险抽样；对身份冲突、全文不足、判尺边界和高频字段做双重核验。任何争议保留为 `unresolved`，直到证据闭合。
