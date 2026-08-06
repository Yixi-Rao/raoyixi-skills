---
name: paper-sentence-deep-read
description: Translate and explain academic papers sentence by sentence for deep personal reading. Use when the user provides an arXiv/OpenReview/conference/PDF URL, local PDF, or paper text and asks for a detailed Markdown file with each paper sentence, Chinese translation, and researcher-level explanation. Especially suited for AI/ML/LLM/RL/agent papers and requests such as "论文逐句精读", "逐句翻译解读", "帮我深入读这篇论文", or "输出到指定文件夹".
---

# Paper Sentence Deep Read

## Purpose

Produce a Markdown deep-reading file for an academic paper. The deliverable is not a summary or review; it is a sentence-by-sentence reading aid that preserves the paper's logical order and explains what each sentence means in the author's argument.

## Workflow

1. Confirm the paper source and output folder. If the user did not specify an output folder, ask for one before writing the final Markdown file.
2. Get the paper from the provided URL, PDF, or local text. For arXiv links, follow the HTML-first extraction rules below. For other sources, prefer primary sources such as OpenReview, publisher pages, or the user-provided local PDF.
3. Extract paper metadata: title, authors, venue if available, year if available, source link, and extraction date.
4. Identify the main paper body. Include Abstract, Introduction, Related Work, Method, Experiments, Analysis, Discussion, Limitations, and Conclusion when present.
5. Skip References, Appendix, Supplementary Material, acknowledgements, author contribution statements, and unrelated publication metadata unless the user explicitly asks for them.
6. Split English prose strictly by sentence-ending periods where reasonable, while protecting common paper constructs such as "Fig.", "Eq.", "et al.", decimals, URLs, abbreviations, citations, formulas, and code-like snippets from broken sentence splits.
7. Process each sentence in original paper order with `Original`, `Translation`, and `Explanation` blocks.
8. Write exactly one `.md` file into the user-specified folder. Use a filename based on the sanitized paper title, such as `<paper-title>_deep_reading.md`.

## ArXiv HTML-First Extraction

For any `arxiv.org` paper URL, extract the paper from arXiv HTML before trying TeX source or PDF.

1. Read the arXiv identifier from the input URL, preserving a version suffix such as `v2` when present.
2. Normalize `/pdf/` and `/abs/` URLs to `/html/`:
   - `https://arxiv.org/pdf/2607.07508` -> `https://arxiv.org/html/2607.07508`
   - `https://arxiv.org/pdf/2607.07508.pdf` -> `https://arxiv.org/html/2607.07508`
   - `https://arxiv.org/abs/2607.07508` -> `https://arxiv.org/html/2607.07508`
3. Fetch the normalized HTML page and extract content from its semantic paper structure. Preserve section order, paragraph order, equations, figure and table captions, and citation context. Exclude navigation, accessibility controls, download links, and unrelated page metadata.
4. Verify that the HTML contains the paper title, abstract, and substantive body sections. Do not treat an error page, conversion warning without paper content, or metadata-only page as a successful extraction.
5. If arXiv HTML is unavailable or materially incomplete, fall back in this order: arXiv TeX source from `/e-print/<id>`, then arXiv PDF from `/pdf/<id>`.
6. Keep the user's original URL as `Source` and record the actual HTML, TeX, or PDF extraction source in `Reading Scope` notes.

## Copyright Boundary

Do not reproduce an entire copyrighted paper verbatim from a web link unless the source license clearly permits it or the user provided the full text/PDF as local content for transformation. If full verbatim reproduction is not allowed, keep `Original` to short compliant excerpts or sentence locators, and still provide faithful Chinese translation and explanation based on paraphrased source understanding. Tell the user briefly when this boundary changes the output shape.

## Output Structure

Use this Markdown structure:

```markdown
# <Paper Title> - 逐句精读

## Paper Information

- Title:
- Authors:
- Venue:
- Year:
- Source:
- Output generated:

## Reading Scope

- Included sections:
- Skipped sections:
- Notes:

# Abstract

## Sentence 1

### Original

<original sentence or compliant excerpt/locator>

### Translation

<accurate Chinese translation>

### Explanation

<researcher-level explanation of what this sentence contributes>
```

Continue with the same structure for each section and sentence.

## Few-Shot Style Example

Match this level of translation accuracy and explanation depth:

```markdown
## Sentence N

### Original

We validate these findings through weak-to-strong reverse distillation, showing that same-family 1.5B and 7B teachers are distributionally indistinguishable from the student's perspective.

### Translation

作者通过弱到强的反向蒸馏实验验证了这些发现，结果表明，从学生模型的视角来看，同一家族的1.5B和7B教师模型在分布上几乎无法区分。

### Explanation

这里的“weak-to-strong reverse distillation”可以理解为一种反向验证实验，用来检验教师模型是否真的向学生提供了新的分布信息。作者发现，如果教师和学生来自同一模型家族，即使参数规模不同，例如1.5B和7B，它们对学生而言可能并没有明显不同。换言之，大模型教师虽然更大，但其输出分布可能仍然落在学生熟悉的模式里，因此不一定能提供有效的新监督信号。

## Sentence N+1

### Original

Probing into the token-level mechanism, we show that successful OPD is characterized by progressive alignment on high-probability tokens at student-visited states, a small shared token set that concentrates most of the probability mass (97%-99%).

### Translation

进一步探查token级别机制后，作者发现，成功的OPD具有这样一个特征：在学生模型访问过的状态上，学生会逐步与教师在高概率token上对齐；这些高概率token构成一个很小的共享token集合，却集中了绝大部分概率质量，即97%到99%。

### Explanation

这句话解释OPD为什么能在微观层面起作用。OPD并不是让学生平均学习教师的整个词表分布，而是在学生自己实际到达的状态上，逐渐学习教师认为最可能的少数几个token。虽然这些token数量很少，但它们占据了教师分布中绝大部分概率，因此对训练影响最大。成功的OPD，本质上表现为学生在关键高概率token上的持续对齐。

## Sentence N+2

### Original

We further propose two practical strategies to recover failing OPD: off-policy cold start and teacher-aligned prompt selection.

### Translation

作者进一步提出了两种实用策略来修复失败的OPD：离线策略冷启动和教师对齐的提示选择。

### Explanation

这里给出了方法层面的贡献。off-policy cold start表示在正式进行on-policy训练前，先用一些非学生当前策略采样的数据进行初始化，使学生更容易进入教师能够发挥作用的状态区域。teacher-aligned prompt selection表示选择更适合教师模型能力发挥、也更容易让学生从教师中获得有效信号的prompt。两者都旨在解决OPD训练失败的问题。

## Sentence N+3

### Original

Finally, we show that OPD's apparent free lunch of dense token-level reward comes at a cost, raising the question of whether OPD can scale to long-horizon distillation.

### Translation

最后，作者指出，OPD表面上像是拥有“免费午餐”般的密集token级奖励，但这种优势是有代价的；这也引出了一个问题：OPD能否扩展到长程任务蒸馏。

### Explanation

这句话指出OPD的潜在局限。OPD看起来很有吸引力，因为它能在token级别提供密集监督信号，比只在最终答案上给奖励更容易训练。但这种密集奖励可能带来额外成本，例如对教师分布的依赖、长轨迹中的误差积累、训练状态分布偏移，以及教师信号是否能在长程推理中持续有效。因此，作者对OPD是否适合长时序、长推理、多步任务蒸馏提出了疑问。
```

## Translation Rules

- Translate into accurate, natural Chinese.
- Preserve the author's meaning and technical claims; do not add critique, speculation, or unsupported claims.
- Keep important English terms on first mention using `English term（中文翻译，abbreviation）` when useful.
- Use the abbreviation or established Chinese term consistently after first mention.
- Keep model names, dataset names, benchmark names, method names, variables, equations, and cited work names in their original form unless a standard Chinese translation exists.
- Do not collapse multiple original sentences into one translation block.

## Explanation Rules

Explain at Level 2: researcher-level interpretation for AI/ML readers with relevant background.

For each sentence, explain only what helps the user understand the paper deeply:

- The sentence's role in the paper's argument.
- The technical meaning of key terms or mechanisms.
- How it connects to nearby context.
- What problem, design choice, experiment, or result the author is establishing.

Do not:

- Write reviewer-style criticism.
- Judge novelty or correctness unless the sentence itself makes that comparison.
- Add unrelated background.
- Repeat the translation in different words.
- Turn the output into a high-level paper summary.

## Formula, Figure, Table, And Algorithm Handling

- Preserve formulas when allowed by the source boundary. Explain variables, objective, and intuition.
- For figures, explain what the figure shows, axes or visual encodings, experimental setup, and the author's intended takeaway.
- For tables, explain metrics, compared methods, key rows/columns, and the author's intended conclusion.
- For algorithms, explain the procedure step by step and how each step supports the method.
- If figure/table content cannot be extracted reliably, state that limitation and explain from captions or surrounding text.

## Quality Checks

Before final response:

- Verify the Markdown file exists in the requested folder.
- Check that References and Appendix were skipped unless requested.
- Check that the first several sentence splits did not break abbreviations, decimals, citations, formulas, or URLs.
- Check that the output follows the repeated `Original` / `Translation` / `Explanation` structure.
- Report the saved file path and any extraction or copyright-scope limitations.
