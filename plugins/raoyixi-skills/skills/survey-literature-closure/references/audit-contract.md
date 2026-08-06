# 闭包审计契约

`scripts/scaffold_survey.py` 生成 `reports/closure_audit.json`。由实际执行器持续更新它，并使用 `scripts/validate_closure.py` 做最终 fail-closed 验收。

## 顶层字段

- `schema_version`：当前为 `1`。
- `skill_version`：生成器、契约、种子清单和验证器必须一致；改变字段或完成语义时提升版本，不兼容升级时先迁移，不得静默补字段。
- `contract_sha256`：`survey_contract.json` 的原始字节哈希。
- `artifacts`：逐字节绑定字段词表、逐篇判读模板和 stage-only mutation plan。
- `topic`、`cutoff`、`phase`：必须与契约一致；成功阶段为 `fixed_point_complete`。
- `seed_manifest`：至少一个种子，用 SHA-256 绑定原始清单，并分别记录 `structure_valid`、`identities_resolved`、`duplicates_resolved` 和来源类别数。脚手架只能证明结构有效，不能预先证明身份或去重完成；来源类别数必须达到契约中的最低值。
- `counts`：唯一节点、边及各分类计数。
- `queues`：screen、expand、refresh 待处理数。
- `fetch`：待处理、失败和未解析抓取数。
- `identity`：身份冲突和重复节点数。
- `evidence`：全文、日期和字段证据缺口。
- `coverage`：可扩展节点数、双方向分页及来源并集状态。
- `refresh`：刷新轮次、新 ID、边快照和孤儿节点。
- `issues`、`dedup`：阻塞问题和输出词表冲突。
- `budget`：保险上限是否触发。
- `delivery`：是否要求外部写入，以及 dry-run/apply/readback 状态。
- `claim`：完成声明是否经过范围限定。

## 更新原则

将审计视为台账的派生结果，不手工把布尔值改成 `true` 来绕过队列。每次生成时从数据库重新计算计数、覆盖和冲突，并绑定契约哈希。

分类计数之和必须等于唯一节点数。`unresolved` 论文、失败分页、未解析引用、身份冲突和字段证据缺口都必须显式出现，不能仅写在自由文本备注中。

## 验证

运行：

```bash
python3 scripts/validate_closure.py \
  --contract /absolute/path/survey_contract.json \
  --seed-manifest /absolute/path/seed_manifest.json \
  --audit /absolute/path/reports/closure_audit.json
```

退出码：

- `0`：结构有效且所有完成门通过；
- `1`：结构有效但仍有阻塞项，或声明尚未提交；
- `2`：JSON、字段类型、契约绑定或完成声明存在结构/一致性错误。

验证器还核对字段词表与契约定义一致、判读模板展开全部 C 谓词和字段、mutation plan 保持 stage-only，并确认原始参考文献明确出现在来源契约中。

验证器输出 `valid`、`operational_complete`、`success`、`blockers`、`errors`、`success_statement_template` 和 `success_statement_usable`。`valid=true` 仅表示 schema、跨工件绑定和完成门输入彼此一致，不表示调研完成；以 `success` 判断完成。仅当 `success_statement_usable=true` 时使用该声明模板。保留该输出作为最终报告附件。

## 外部写入

若 `survey_contract.json` 中 `delivery.required=true`，成功还要求：

- `dry_run_verified=true`；
- `applied=true`；
- `readback_missing/readback_duplicates/readback_mismatches=0`；
- `protected_field_changes=0`。

只读计划不得设置 `applied=true`。如果用户允许先交付中间结果，保持 `claim.success=false`，并把结果明确标为快照或阶段性清单。
