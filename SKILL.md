---
name: autoresearch-blog
description: Iteratively improve and judge a blog post with explicit keep/discard decisions, experiment logging, resume support, target score confirmation, and a max-iteration budget via autoresearch-blog, autoresearch-blog:N, or autoresearch-blog:continue.
---

# autoresearch-blog

这个 skill 用来对单篇 blog 草稿做有限预算的迭代优化。核心不是“无限润色”，而是围绕一个明确目标分数，在最多 `N` 轮内判断文章是否值得继续优化、是否已经达到目标、以及哪一版应该被保留。

这个 skill 还必须把实验状态写到磁盘。没有持久化状态，就没有真正的 autoresearch，只是一次性人工润色。

## 1. Invocation

- `autoresearch-blog`
  - 使用默认最大迭代次数 `3`
- `autoresearch-blog:N`
  - `N` 表示最大迭代次数
  - `N` 必须是正整数
  - 建议范围 `1-10`
  - 若用户给出过大的数字，也应提醒收益递减和时间成本
- `autoresearch-blog:continue`
  - 继续最近一次未完成，或用户明确指定要继续的实验
  - 默认再追加 `3` 轮预算，而不是重置总历史
- `autoresearch-blog:continue:N`
  - 在继续已有实验的前提下，再允许最多 `N` 轮新增迭代
  - `N` 只表示这次追加预算，不覆盖实验历史中的已用轮数
- `autoresearch-blog:continue:N@TARGET`
  - 在继续已有实验的前提下，再允许最多 `N` 轮新增迭代，并把目标分数改为 `TARGET`
  - 例如：`autoresearch-blog:continue:3@90`
  - `TARGET` 按 `0-100` 计
  - 若显式提供了新 target，必须先确认，再更新实验状态

## 2. Experiment State on Disk

每次正式实验都必须在仓库根目录下写入 `.autoresearch-blog/`。建议结构：

```text
.autoresearch-blog/
  active_experiment.json
  experiments/
    <experiment_id>/
      meta.json
      state.json
      results.jsonl
      progress.svg
      versions/
        v0.md
        v1.md
        ...
```

各文件职责：

- `active_experiment.json`
  - 指向当前默认继续的实验
- `meta.json`
  - 保存文章路径、experiment id、创建时间、target、初始上下文
- `state.json`
  - 保存当前最佳版本、当前分数、已用迭代数、剩余预算、是否达标、停止原因
- `results.jsonl`
  - 每轮一条记录，追加写入，不覆盖历史
- `progress.svg`
  - 从 `results.jsonl` 渲染出的实验进度图
  - 用来直观看 `keep / discard / target-change / score trend`
- `versions/vN.md`
  - 只保存 `baseline` 和被 `keep` 的版本全文

默认不要为每个 `discard` 版本保存完整全文。对大多数 blog 实验来说，这些全文会快速堆积，但对后续决策帮助有限。

磁盘状态是 source of truth。继续实验时，必须先读磁盘，再决定下一轮做什么。不要依赖对话记忆。

## 3. Required Preflight

每次开始一个新的 blog 优化任务前，必须先确认以下信息，再进入正式迭代：

- `target_score_percent`
  - 这是目标分数，按 `0-100` 计
  - 不允许静默假设
  - 必须显式向用户确认，例如：`本次 target 是 85/100，对吗？`
- `max_iterations`
  - 来自 `autoresearch-blog:N`
  - 若未提供则默认 `3`
- `target_audience`
  - 如果从文章中无法稳定推断，就应补问
- `core_question`
  - 如果标题和正文不足以判断，也应补问
- `editing_goal`
  - 明确这次任务的主要目标是：
    - `insight_blog`：提升论点、结构、证据和表达
    - `humanizer`：减少 AI 写作痕迹，同时保留原意、信息密度和作者声音
  - 如果用户说的是“去 AI 味”“更像人写的”“humanize”，默认应推断为 `humanizer`
- `document_language`
  - 明确当前文稿的主语言，至少区分 `zh` 和 `en`
  - 如果文稿语言本身清楚，可以直接推断；如果是双语草稿或混合草稿，应显式确认
- `challenge_set`
  - 在正式实验前，固定 3-5 个阅读挑战或失败探针，后续每轮都用同一组探针复评
  - 不要每轮临时换问题，否则很难比较修改是否真的有效
  - 对 blog，推荐从下面几类里选：
    - 读者能不能用一句话复述主论点
    - 读者能不能指出证据边界和不确定性
    - 读者能不能说出 2-3 个可迁移判断
    - 某一段是否存在明显术语过载或中英混杂
    - 标题、开头、结尾是否共同服务于同一个核心判断
  - 如果 `editing_goal = humanizer`
    - 至少额外加入这两类挑战：
      - 这段文字还有哪些地方“明显像 AI 写的”
      - 为了去 AI 痕迹，这轮修改有没有把原意、具体性或作者声音一起削掉

如果用户只给了 `autoresearch-blog:N`，但没有给 target，就先确认 target，再开始 baseline judge。

如果用户要求 `continue`：

- 优先读取 `.autoresearch-blog/active_experiment.json`
- 若存在多个候选实验且无法唯一判断，应让用户指定
- 若历史实验已经 `target_met = true`，也可以继续，但必须提示这是在“达标后继续优化”，收益可能很低
- 若命令里带了 `@TARGET`，则这是一次显式 target 变更：
  - 必须先确认新 target
  - 确认后更新 `active_experiment.json` 和 `state.json`
  - 并在 `results.jsonl` 追加一条 `target-change` 事件

## 4. Judge Contract

评分标准以 `judge.md` 为准。这个 skill 不自己发明第二套标准。

在任何一轮里，若出现以下情况，应优先尊重 judge 结果，而不是为了追求“完成 N 轮”继续机械改写：

- 命中 `hard gate`
- 新版本总分更高，但高权重维度变差
- 新版本更顺滑，但明显更空、更泛、更不像作者本人

同时要明确区分两件事：

- `discard`：这一轮候选版本不被采纳
- `stop`：整个实验停止

`discard` 不等于 `stop`。只要还没达到 target，且本次预算还没用完，即使这一轮分数下降，也应丢弃该轮结果并继续下一轮。

## 5. Baseline Setup

新实验开始时，必须先做以下落盘动作：

1. 生成 `experiment_id`
2. 创建实验目录
3. 将原稿保存为 `versions/v0.md`
4. 做 baseline judge
5. 把 baseline 结果写入 `state.json` 和 `results.jsonl`
6. 更新 `active_experiment.json`

baseline 不是口头描述，必须是可恢复的实验起点。

baseline 完成后，还要做一次 checkpoint：

- 如果 `baseline_score >= target_score_percent`
  - 明确提示用户文章已经达标，确认是否还要继续做高位微调
- 如果 `score_gap_to_target <= 2`
  - 明确提示这已经进入高位微调区间
  - 后续收益很可能主要来自证据扩展、结构强化或 framing 调整，而不只是语言润色
- 不论是否提示，只有在用户要求开始实验时，才进入正式迭代

## 6. Iteration Loop

对每次任务，按以下顺序执行：

1. 从磁盘读取 `state.json`、最近若干条 `results.jsonl`、当前最佳版本
2. 产出当前分数、目标分数、距离目标的差距
3. 用百分比提示当前进度
4. 只挑 1-3 个最高杠杆问题进行修改
5. 生成候选新版本
6. 重新 judge
7. 将本轮结果追加到 `results.jsonl`
8. 如果 verdict 是 `keep`，再把该版本保存到 `versions/vN.md`
9. 根据 `keep/discard` 规则决定是否更新 `state.json` 中的最佳版本
10. 如果本轮 `discard`，回到当前最佳版本继续下一轮，而不是停下
11. 重新渲染 `progress.svg`
12. 只有在达到 target 或用完本次预算时才停止

不要在一轮里同时改十个方向。优先级应是：

1. `thesis clarity`
2. `evidence / epistemic honesty`
3. `insight density`
4. `structure`
5. 其他局部 prose 问题

如果 `editing_goal = humanizer`，则在不破坏前四项的前提下，还要显式检查：

- 是否减少了明显的 AI 写作痕迹
- 是否保住了原意，而不是只把句子改得更粗糙
- 是否保住了具体性，而不是把文本改成另一种空泛
- 是否保住了作者声音，而不是从“AI 腔”变成“模板化人类腔”

对不同语言的 blog，局部 prose 问题还包括对应的默认语言规则：

- 如果 `document_language = zh`
  - 除必要术语、专有名词、代码标识符、引用原词外，优先保持自然中文表达
  - 不要把普通英文词混进中文句子里制造“半翻不翻”的文风
  - 如果必须保留英文术语，应尽量集中在真正需要精确保留的点，而不是让整段都变成中英夹写
- 如果 `document_language = en`
  - 优先保持自然、习惯的英文表达，而不是逐句翻译式英语
  - 避免不必要的术语膨胀、名词链堆叠和抽象化表达
  - 避免在同一段里混用论文腔、产品营销腔和口语说明腔，导致 register 漂移
  - 如果必须保留非英文术语，也应让它服务于精度或引用，而不是让正文变成多语言拼接

### Mutation Contract

每轮修改都应先写清楚一个 `mutation_hypothesis`：这轮为什么值得改，预期会改善什么失败模式。

推荐的好 mutation：

- 提前放出被埋得太深的主论点
- 把一串平铺术语改成“归类 + 例子”
- 删掉让文章更长但不增加判断力的句子或段落
- 给高风险判断补边界、补样本限制、补证据说明
- 把标题、开头、结尾重新拉回同一个核心判断
- 如果 `editing_goal = humanizer`
  - 用更具体的事实替换“重要性”“意义”“转折点”之类的空泛拔高
  - 把 vague attribution 改成具体来源或直接删掉
  - 去掉明显的 chatbot residue、servile tone、generic positive conclusions
  - 把 present-participle 假深度、rule of three、copula avoidance、过多 em dash 等模式改回自然表达
  - 在不失真的前提下恢复具体态度、真实犹豫和节奏变化

默认避免的坏 mutation：

- 整篇重写
- 一轮里同时改五个方向，导致无法判断为什么变好或变坏
- 只让 prose 更顺，却不增强论点、证据或结构
- 为了迎合 judge 而写出更空、更模板化的文章
- 明明是证据不足，却只做术语替换或标点美容
- 如果 `editing_goal = humanizer`
  - 只是把一套 AI 词换成另一套 AI 词
  - 为了“像人写的”强行加入假情绪、假个性或无关口语
  - 一味打碎句子，让文本变得粗糙但并没有更自然
  - 去掉 AI 痕迹的同时，也去掉了信息密度、精度或作者声音

如果某轮改动无法用一句清晰的 `mutation_hypothesis` 描述，通常说明这轮改动范围太散，不应继续。

如果 `editing_goal = humanizer`，每轮在最终 judge 前，还应做一次简短的 anti-AI audit：

1. 先问：`What still makes this text obviously AI-generated?`
2. 用 3-5 条短 bullet 写出剩余 tell
3. 再只针对这些 tell 做最后一轮小修
4. 不要因为这次 audit 而重写全文

## 7. Progress Reminder Format

每轮都要显式提醒用户当前进度，使用百分计。

推荐格式：

```text
Iteration 2/5 | score 78.0 -> 82.5 | target 85.0 | progress 97.1% | verdict keep
```

其中：

- `progress = min(current_score / target_score_percent * 100, 100)`
- 保留一位小数即可
- 如果 target 已达成，明确写出 `target reached`

任务开始时也要先报一次：

```text
Target confirmed: 85.0/100 | Max iterations: 5 | Baseline evaluation starts now
```

如果是继续实验，建议格式：

```text
Continuing experiment exp-20260324-001 | used 1 iterations | additional budget 3 | current score 86.5 | target 85.0
```

## 8. Stop Conditions

满足任一条件才可停止：

- `current_score >= target_score_percent`
- 已达到最大迭代次数 `N`

如果是 `continue` 模式，这里的“最大迭代次数”指本次追加预算，而不是历史总轮数。

下面这些情况都不应触发提前停止：

- 连续多轮 `discard`
- 分数下降
- judge 认为后续收益递减
- 当前 best 已经高于旧 target，但低于新 target

这些信息只应影响下一轮改什么，不应改变“继续跑到 target 或预算耗尽”的硬规则。

## 9. Result Logging Schema

`results.jsonl` 中每行至少包含：

```json
{
  "iteration": 1,
  "version_id": "v1",
  "parent_version_id": "v0",
  "overall_score": 86.5,
  "target_score_percent": 85.0,
  "progress_percent": 100.0,
  "score_gap_to_target": 0.0,
  "verdict": "keep",
  "store_full_version": true,
  "target_met": true,
  "changed_focus": [
    "thesis clarity",
    "experiment boundary",
    "ending transferability"
  ],
  "mutation_hypothesis": "Making the thesis explicit in the opening will reduce reader uncertainty and improve thesis clarity without flattening the voice.",
  "failure_pattern": "Main claim appears too late, so readers cannot quickly state what the article is arguing.",
  "strengths": [
    "The main thesis is explicit earlier"
  ],
  "must_fix": [
    "Title can still be sharper"
  ],
  "diff_summary": [
    "Added a one-sentence thesis near the opening",
    "Clarified that the OpenClaw section is not a multi-framework benchmark"
  ],
  "summary": "Reached target after sharpening thesis and tightening experiment framing.",
  "timestamp": "2026-03-24T17:40:00+08:00"
}
```

字段约定：

- `store_full_version = true`
  - 只用于 `baseline` 和 `keep` 版本，表示该版本全文应保存在 `versions/`
- `store_full_version = false`
  - 默认用于 `discard` 版本，只保留结构化日志
- `diff_summary`
  - 用 1-5 条短句总结本轮相对父版本的主要变化
  - 这是 `continue` 时的重要上下文，不要省略
- `mutation_hypothesis`
  - 用一句话说明这轮改动在赌什么提升
  - 例如：`Grouping jargon into categories will reduce reader load without weakening precision.`
- `failure_pattern`
  - 用一句话说明这轮主要在修什么失败模式
  - 例如：`Readers cannot tell whether the article lacks evidence or only hides it too deep in the middle sections.`

如果是 target 变更事件，允许写成另一种记录：

```json
{
  "event": "target-change",
  "from_target_score_percent": 85.0,
  "to_target_score_percent": 90.0,
  "reason": "User requested a higher bar during continue mode.",
  "timestamp": "2026-03-24T18:20:00+08:00"
}
```

如果某一轮是分数下降后的 `discard`，也必须写入 `results.jsonl`。只是：

- `store_full_version = false`
- 不更新 best version
- 下一轮从当前 best 继续

## 10. Final Output

结束时至少要给出这些信息：

- 最终保留的是第几版
- `final_score`
- `target_score_percent`
- `target_met`
- `iterations_used`
- `discard_count`
- 本轮最有效的改动是什么
- 还有哪些问题没有解决，但不值得继续改

## 11. Continue Semantics

当用户说“继续实验”时，不要重复 baseline，也不要重写历史。应该：

1. 读取当前 active experiment
2. 找到 `state.json` 中的最佳版本
3. 读取最近几轮 `results.jsonl`
4. 基于未解决问题继续下一轮
5. 将新一轮作为新的 `version_id` 追加

如果用户没有显式要求新实验，优先继续已有实验，而不是偷偷新建一个。

如果某轮出现分数下降：

1. 记录为 `discard`
2. 不覆盖当前 best
3. 不提前停止
4. 继续用剩余预算跑下一轮

如果用户使用 `autoresearch-blog:continue:N@TARGET`：

1. 先解析出追加预算 `N` 和新目标 `TARGET`
2. 读取当前 active experiment
3. 显式确认新 target
4. 将 target 变更写入状态和日志
5. 再开始新的追加迭代

## 12. Retention Policy

为了减少版本噪音和上下文负担，默认采用下面的保留策略：

- 永久保留全文
  - `baseline`
  - 当前 `best`
  - 所有 `keep` 版本
- 默认不保留全文
  - `discard` 版本
- `discard` 至少保留
  - 分数
  - verdict
  - `changed_focus`
  - `must_fix`
  - `diff_summary`
  - 父版本 id

只有在以下情况下，才为 `discard` 版本额外保留全文：

- 这是一次高信息量失败，暴露了重要的 Goodhart 模式
- 分数显著下降，值得回放
- 用户明确要求完整保留

## 13. Author-Preservation Rule

这个 skill 的目标是增强文章，不是把文章改写成通用 AI blog。

因此在每轮判断里，都要问一句：

- 新版本是否更清楚？
- 新版本是否更扎实？
- 新版本是否还像原作者？
- 如果 `document_language = zh`，它是否仍然像自然中文写作，而不是中英混杂的迁移文风？
- 如果 `document_language = en`，它是否仍然像自然英文写作，而不是翻译腔、术语膨胀或 register 漂移后的英文？

如果第三条开始明显变差，即使前两条略有提升，也要谨慎 `keep`。
