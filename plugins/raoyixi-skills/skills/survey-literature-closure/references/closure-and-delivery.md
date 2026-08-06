# 引用图闭包、失败处理与交付

## 1. 使用两个持久化队列

维护 `screen_queue` 和 `expand_queue`，并为固定点刷新维护独立 `refresh_queue`。节点至少记录身份、分类、层级、发现路径、全文状态、判定证据和最后处理版本；边记录方向、provider、分页快照和原始标识。

循环执行：

```text
while screen_queue or expand_queue:
    screen one node from original full text
    if classification in {core, adjacent, unresolved}:
        fetch every references page and every cited-by page
        union original bibliography, Semantic Scholar, and OpenAlex
        canonicalize identities and enqueue unseen nodes
    else:
        keep excluded node as a leaf
    commit node, edges, cursors, attempts, and paths atomically
```

不要用递归调用栈承载状态；使用可恢复的 BFS 队列和唯一身份集合。

## 2. 证明来源覆盖

对每个可扩展节点、每个方向、每个声明来源记录：

- 未开始、处理中、完成、明确未收录、失败或待重试；
- 当前 cursor/page、累计 items 和 provider 声明总数；
- 请求时间、快照标识、重试次数和错误；
- 该来源返回的边及其身份解析状态。

至少要求 references 和 cited-by 各有完整来源证据。将多来源结果取并集；一个来源返回空不能掩盖另一个来源失败。

## 3. 有界失败，不伪造成功

- 对 429/5xx 使用指数退避并持久化 checkpoint；采用范围契约中的单-checkpoint 重试上限，默认六次。
- 尊重 provider cooldown；不要忙等或把冷却解释成“无结果”。
- 在主索引失败时切换另一索引，但保留失败状态。
- 将无法取得完整原文、分页不完整、强身份冲突和无法解析的引用加入阻塞项。
- 每篇处理后提交事务；中断后恢复 processing lease，不重复已完成页面。

节点上限和墙钟上限只是保险。触发后停止外部副作用，保存断点，报告未完成并说明需要的预算或外部输入。

## 4. 执行完整固定点刷新

普通队列清空且无待定/失败/冲突后，对全部 `core`、`adjacent` 和 `unresolved` 节点重新抓取两个方向的全部分页：

1. 将本轮边保存为独立 observation，不立即删除历史边。
2. 仅在整轮来源覆盖完整后，对账当前快照。
3. 若出现任何新 ID，回到普通筛选/扩展阶段。
4. 检查被当前索引撤回的边是否产生无发现路径的孤儿节点。
5. 只有完整一轮新增 ID 为零、边快照已对账且孤儿为零，才认定固定点。

## 5. 同时满足成功门

要求：

1. screen、expand、refresh 待处理均为零；
2. queued、unresolved、fetch pending/failed 均为零；
3. 所有可扩展节点的双方向分页完整；
4. 身份冲突、重复节点、阻塞 issue 和字段证据缺口均为零；
5. 完整刷新新增 ID 为零，边快照完成对账，无孤儿节点；
6. 应急预算未触发；
7. 若要求外部写入，dry-run、正式写入和完整回读全部通过。

使用 `scripts/validate_closure.py` 机械检查这些条件，不凭人工浏览计数宣布完成。

## 6. 安全交付

先输出本地证据包：范围契约、种子、节点/边台账、逐篇判断、字段词表、失败清单、层级统计和发现路径。然后生成只读 mutation plan。

写入表格或数据库时：

- 重新读取实时 schema、视图和现有选项；
- 优先 create-only/append-only；
- 把 semantic alias 映射到既有选项；
- 不修改未授权或受保护字段；
- 写后逐行回读新记录，并验证旧记录和旧选项未变化。

写入长文档时，先建章节骨架，再按章节写入；回读大纲、关键字段和链接。复杂图表还要做视觉检查。API 成功只证明请求被接受，不证明读者侧成品正确。

## 7. 限定完成声明

声明应包含题材、截止日期、实际原文来源、图索引并集和“相关子图”限定，并明确不覆盖所有来源均未收录的工作。若只完成清单或快速扫描，改用对应的有限覆盖表述。
