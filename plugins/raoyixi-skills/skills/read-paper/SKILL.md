---
name: read-paper
description: Use when the user asks to read, summarize, explain, analyze, critique, compare, translate, extract details from, write about, or answer questions about a research paper, including when they provide an arXiv/Hugging Face/OpenReview/PDF URL, a paper title only, a local/uploaded paper file, or an existing notes document. Always trigger even if there is already a prior summary or document about the paper; the assistant must read the original paper before answering paper-specific content.
---

# Read Paper

## Non-Negotiable Rule

Do not answer paper-specific facts before reading the original paper. Never rely on model memory, prior notes, blog posts, README files, news articles, Zhihu posts, slides, or an existing interpretation document as a substitute for the original paper.

If the paper has not been opened and read in this turn, first obtain and read the original source. If the original source cannot be accessed, say so and do not present paper content as known.

## Source Acquisition

Follow the user's provided source first:

1. If the user gives a paper URL, open it directly.
2. If the URL is an arXiv abstract or PDF URL, prefer the HTML page:
   - `https://arxiv.org/abs/xxxx.xxxxx` -> `https://arxiv.org/html/xxxx.xxxxx`
   - `https://arxiv.org/pdf/xxxx.xxxxx` -> `https://arxiv.org/html/xxxx.xxxxx`
3. If arXiv HTML is unavailable or incomplete, use the arXiv PDF.
4. If the user gives only a title, search the web for the paper, then open the original paper page or PDF. Prefer primary sources such as arXiv, publisher pages, OpenReview, ACL Anthology, NeurIPS/ICML/ICLR proceedings, DOI pages, or authors' official paper PDFs.
5. If the user provides a local/uploaded PDF or text, read that file as the original source.
6. Existing summaries, Feishu/Notion docs, blog posts, README files, and comments may be used only as context for the user's intent, not as evidence for paper facts.

## Reading Depth

Read according to the task, but state the scope if it is partial.

- For full summaries, technical explainers, article writing, presentations, literature reviews, or critique: read the abstract, introduction, method, experiments, results, limitations/discussion if present, and conclusion. Inspect relevant figures, tables, formulas, algorithms, appendices, and cited evidence as needed.
- For a narrow question: read the sections directly relevant to the question, plus enough surrounding context to avoid misrepresenting the paper.
- For claims about experiments: inspect the relevant tables, figures, metrics, datasets, baselines, and settings.
- For claims about methods: inspect the method section, formulas, algorithm boxes, diagrams, and implementation details if provided.
- If only part of the paper was read, explicitly say which sections/pages were read and avoid conclusions about unread sections.

## Answering Rules

When answering:

1. Be faithful to the paper text.
2. Separate "the paper states/shows" from "my analysis/inference".
3. Do not overstate the authors' contribution.
4. Do not treat other papers, background knowledge, blog explanations, or common practice as content of this paper.
5. Do not generalize experimental results to settings the paper did not test.
6. Do not invent datasets, metrics, numbers, tables, formulas, ablations, failure cases, limitations, implementation details, or conclusions.
7. For key facts, cite the location in the paper when possible: section name, page, figure, table, equation, algorithm, appendix, or the exact source passage in paraphrase.
8. If evaluating the paper, first identify the textual or experimental basis in the paper, then give analysis.
9. If the original paper does not specify something, say "论文中没有说明" or "我没有在原文中找到该信息".
10. If a claim is an assistant inference, label it as inference and explain what paper evidence it depends on.

## Prohibited Behavior

Never:

- Answer paper content without opening the original paper.
- Use memory of a known paper for concrete paper details.
- Write a complete explanation from only the title or abstract.
- Use a blog, Zhihu article, README, news release, slide deck, existing Feishu/Notion doc, or prior summary instead of the paper.
- Infer the method from the title or field conventions.
- Fabricate experimental results, contribution points, limitations, formulas, data processing details, or implementation details.
- Pretend the paper was read when it was inaccessible.
- Present "usually", "generally", "probably", or "may be" as a paper fact.
- Describe the assistant's own interpretation as the authors' stated view.

## If the Paper Cannot Be Accessed

Report access failure clearly:

- List the sources attempted.
- State which sources failed or were inaccessible.
- Say that the current answer cannot reliably cover paper content without the original.
- Ask the user to provide a PDF, screenshots, copied text, or another accessible link.

Do not fill the gap with guesses.
