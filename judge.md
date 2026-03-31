# autoresearch-blog judge

这个文件不是在判断一篇 blog 能不能“爆”，而是在判断它是否对目标读者真正有价值，且这种价值是否足够稳定，值得在反馈实验里被 `keep`。

`autoresearch` 里有一个单一指标 `val_bpb`，而 blog 没有这么干净的 ground truth。所以这里不要追求伪精确的单指标，而要用：

- `hard gates`：拦住明显不该保留的稿子
- `weighted rubric`：衡量一篇文章的综合质量
- `keep/discard rules`：服务于迭代实验，而不是服务于一次性打分

## 1. 先定义评估上下文

在打分前，先显式写出这四项。没有上下文，`relevance` 和 `quality` 很容易飘。

- `target_audience`：这篇文章写给谁
- `core_question`：它要回答什么问题
- `main_claim`：它最核心的一条判断是什么
- `desired_reader_outcome`：读者读完后，应该获得什么新的理解、判断或行动能力
- `document_language`：文稿主语言，至少区分 `zh` 和 `en`
- `editing_goal`：本次任务主要是 `insight_blog` 还是 `humanizer`

默认假设：`autoresearch-blog` 当前主要服务于技术分析 / 观点型 blog，而不是 SEO 拼装文、资讯搬运或营销软文。

## 2. Hard Gates

只要命中任意一条，默认就不应 `keep`，除非修复后重评。

### 2.1 Thesis failure

- 读完前 25% 仍然无法明确文章到底在回答什么问题
- 标题、开头、正文核心论点彼此不一致
- 文章像是在“围绕一个话题说话”，而不是在推进一个明确判断

### 2.2 Evidence failure

- 存在关键事实性判断，但没有证据、例子、实验或一手观察支撑
- 把推测写成结论，把相关性写成因果
- 数字、成本、性能、行为路径等关键说法无法追溯来源

### 2.3 Originality failure

- 全文主要是在复述常识、转述别人结论，缺少作者自己的观察或抽象
- 即使表达流畅，读者读完仍然得不到新的判断框架

### 2.4 Structure failure

- 段落顺序可以随意打乱而不影响理解，说明结构没有真实承担推理职责
- 存在大段重复、跳跃、堆砌，读者需要自己重建作者逻辑

### 2.5 Trust failure

- 语气明显夸张、营销化、过度确定
- 故意回避限制条件、反例、样本边界或不确定性

## 3. Weighted Rubric

每个维度先打 `0-5` 分，再按权重折算成总分 `0-100`。

计算公式：

`weighted_score = sum(raw_score / 5 * weight)`

### 3.1 Audience Fit and Thesis Clarity — 15

看这篇文章是否从一开始就对准特定读者，并提出清晰、可检验的中心判断。

- `0`：主题和受众都不清楚
- `3`：主题明确，但判断不够锋利，受众边界较宽
- `5`：目标读者、核心问题、中心判断都非常清晰，开头就建立了阅读预期

### 3.2 Insight Density and Originality — 20

看文章是否真的有作者自己的观察、抽象、比较或框架，而不是只在复述公共知识。

- `0`：基本无新意
- `3`：有局部新观点，但密度不高
- `5`：多个关键段落都提供了非平庸的新判断，读者能明确感到“这不是随便哪里都能读到的”

### 3.3 Evidence, Accuracy, and Epistemic Honesty — 20

看核心判断是否被真实支撑，以及作者是否诚实地区分观察、推断和猜测。

- `0`：关键论断缺乏支撑，甚至存在明显不实或误导
- `3`：大部分判断有支撑，但仍有若干跳步或边界不清
- `5`：关键论断都有足够证据或一手经验支撑，限制条件和不确定性也被如实交代

### 3.4 Structure and Narrative Flow — 15

看文章是否有明显的推进关系，而不是一串还算顺的段落。

- `0`：结构混乱
- `3`：大体可读，但局部存在重复、跳转或节奏失衡
- `5`：每一节都在推进上一节，读者能自然跟上推理链；如果作者前文承诺了“有三点 / 两个层面 / 几个问题”，后文也会用显式结构把这些承诺兑现

对技术 blog，结构不仅是“有标题”，还包括“结构信号和实际展开一致”。例如：

- 较差写法：前文说“有三件事”，后文却只给一串未编号并列项
- 较好写法：前文给出数量承诺，后文立刻用“第一 / 第二 / 第三”或等价结构承接

### 3.5 Clarity, Readability, and Compression — 10

看表达是否清楚、压缩是否得当，是否在保持信息密度的同时避免晦涩和废话。

- `0`：难读、绕、信息组织差
- `3`：可读，但仍有冗余句、模糊代词、过长段落、术语负担，或标点使用不稳定
- `5`：表意直接、句子干净、信息密度高，几乎没有可删而不伤内容的部分；遇到专业术语时，会优先用“归类 + 例子”帮助读者建立理解路径，而不是平铺一串名词；标点也服务于节奏和结构，而不是制造阅读噪音

对技术 blog，下面这种区别应被明确打分：

- 较差写法：在一个句子里平铺很多不同层级的专业名词，让读者自己猜它们之间的关系
- 较好写法：先把术语按类别分组，再给 1-2 个代表性例子，让读者先获得结构，再吸收细节

语言层检查应随 `document_language` 切换，而不是默认只按中文评。

如果 `document_language = zh`，还应额外检查：

- 中英文标点混用但没有节奏或语义上的理由
- 引号、括号、破折号、冒号的使用前后不一致
- 句子本身已经很重，却再叠加过多逗号、分号或插入语，导致阅读断裂
- 英文术语已经增加理解负担时，标点还在进一步放大这种负担
- 除必要术语、专有名词、代码标识符、引用原词外，默认不鼓励中英混杂表达
- 如果一句话完全可以用自然中文表达，却混入 `turn`、`conversation`、`explanation` 这类普通英文词，应扣分
- 英文术语可以保留，但要尽量让它落在真正需要保留的地方，而不是扩散成整段混杂文风
- 目标不是“把所有英文都翻掉”，而是让中文正文仍然像中文作者在写作，而不是像长期在英文语境里思考后直接混写出来的文本

对当前这个 `autoresearch-blog` 项目里的中文技术文章，还应进一步收紧一条：

- `side effect`、`observability layer`、`cost shift`、`implicit loops`、`queue handoff`、`deferred work` 这类词组，如果上下文完全可以自然中文化，默认应视为待优化项，而不是“技术味”
- 只有在翻译后会显著损失精度、或原词本身就是引用对象时，才保留英文表达

如果 `document_language = en`，还应额外检查：

- 句子是否带明显翻译腔，而不是自然英文
- 是否堆叠过多名词链、抽象名词或 Latinate 词汇，让句子显得笨重
- 是否出现不必要的 jargon inflation，本可直接说明却写成更“专业”的空洞表达
- 是否在同一段里混用论文腔、营销腔、口语说明腔，导致 register 不稳定
- 标点是否帮助切开复杂句，而不是让句子变成一长串几乎没有层次的 clause chain
- 如果保留非英文术语，它是否真的服务于精度、引用或上下文，而不是制造异物感

如果 `editing_goal = humanizer`，还应额外检查：

- 文本是否还残留“明显像 AI 写的”痕迹，而不是只看它是否通顺
- 去掉 AI 痕迹之后，是否仍然保住了原意、具体性和信息密度
- 修改是否只是把一种 AI 腔换成另一种 AI 腔
- 作者是不是先在做防御性澄清、边界管理和误解预防，而不是先把真正的观察和判断说出来
- 句子是不是把本来可以直接成立的判断补成了层层转折和完整说明，读起来像在交代、像在答题，而不是像作者在下判断

对中文 humanizer，优先检查这些模式：

- 空泛拔高：动不动就是“重要”“深刻”“关键”“不只是……更是……”
- 套话式转折：`归根结底`、`某种程度上`、`值得注意的是` 被机械重复
- 模板化总结：结尾只是在情绪上收束，却没有新的判断
- 过度平滑：每句都太圆，几乎没有真实停顿、犹豫和轻重变化
- 中英混杂被拿来伪装“专业感”
- 免责声明腔：`这里先把边界说清楚`、`不是 A，也不是 B，只是 C` 这类结构反复出现，像在预防审稿人误解
- 交代过满：本来一句就能说清的判断，被补成了过于完整的解释链和标准转折
- 否定式对举过密：`不是 A，而是 B`、`不是因为 A，而是因为 B`、`既不是 A，也不是 B` 这类句式在同一篇里反复出现，读起来像模型在制造“转折感”而不是作者真的需要这样组织判断
- `前者 / 后者` 过密：反复用抽象对举词承接论点，像在写标准答案，而不是自然展开判断
- 机械三段并列：连续使用 `第一 / 第二 / 第三`、或过于工整的三项并列，把散文写成了伪装过的列表
- 解释节奏过匀：反复出现“先定义一句，再展开一句，再补一句总结”的固定段落节奏，读者很快能猜到下一句
- 短句碎片化：明明是一个连续判断，却被切成很多过短的句子或小段，只是为了制造“有力”的错觉
- 抽象名词堆叠：`系统`、`行为`、`路径`、`视角`、`因果链`、`可观测性` 这类词连续密集出现，句子听起来像概念压缩，而不是作者在说具体观察

对这类中文 humanizer，一个常见的较好写法是：

- 先说自己看到了什么，再说这意味着什么
- 少做预防性澄清、边界管理和误解预防
- 允许句子有轻重变化，而不是把每个转折都补到非常完整

对英文 humanizer，优先检查这些模式：

- inflated significance：把普通判断包装成重大转折或深远意义
- promotional language：听起来像 ad copy、thought leadership 或 keynote prose
- vague attribution：`experts say`、`many believe`、`it is often argued` 这类没有责任主体的说法
- formulaic structure：`Challenges and Opportunities`、`Looking Ahead`、`In today's fast-paced world` 这类模板标题或段落
- AI vocabulary / synonym cycling：不停用显得“聪明”的词替换简单词
- copula avoidance：能直接写 `X is Y` 却强行绕成更抽象的句子
- rule of three / negative parallelism overuse：一遍遍出现刻意工整的三连句和 `not X, not Y, but Z`
- formatting artifacts：过多 em dash、bold、title case 小标题，像在刻意制造“写作感”
- chatbot residue：`I hope this helps`、`as an AI`、knowledge-cutoff residue、servile framing
- generic uplift ending：结尾气氛很正面，但没有新增判断

### 3.6 Actionability or Transferable Takeaways — 10

并不是每篇 blog 都要给 checklist，但读者读完后应该能带走可复用的判断、方法或设计启发。

- `0`：读完没有获得可迁移的东西
- `3`：有结论，但可迁移性一般
- `5`：文章明确改变了读者的分析框架、设计判断或实践方式

### 3.7 Voice and Memorability — 5

看文章是否有作者自己的声音，而不是标准化 LLM prose。

- `0`：高度模板化、无辨识度
- `3`：有局部个性，但整体仍偏通用
- `5`：语气、节奏、比喻、句式选择都具有明显作者风格，且不影响严肃性

如果 `editing_goal = humanizer`，这里还要额外注意一条：

- 目标不是“更像某种抽象的人类写作”，而是“更少 AI 痕迹，同时仍然像这个作者”

### 3.8 Title, Opening, and Ending Quality — 5

看标题是否准确，开头是否抓住问题，结尾是否完成收束与提升。

- `0`：标题失真，开头拖沓，结尾空泛
- `3`：基本合格，但仍偏平
- `5`：标题准确有力，开头迅速建立 tension，结尾能把判断抬高一层

## 4. Diagnostic Counters

这些指标不是主分数，但适合在实验回路里做辅助对比，防止 judge 只给抽象评语。

- `unsupported_claim_count`：没有支撑的关键论断数量
- `concrete_evidence_count`：实验、数字、代码路径、日志、案例等具体证据数量
- `original_insight_count`：不是常识复述的关键判断数量
- `actionable_takeaway_count`：读者可直接迁移的设计判断或方法数量
- `filler_sentence_count`：删掉后几乎不影响信息传递的句子数量
- `jargon_without_explanation_count`：未经解释就直接使用的术语数量
- `term_stack_without_grouping_count`：同一句或同一小段中堆叠多个专业术语，但没有做归类、转译或举例的次数
- `punctuation_issue_count`：标点不一致、节奏失衡，或标点选择放大了阅读负担的次数
- `mixed_language_phrase_count`：偏离文稿主语言的表达被混入正文并增加违和感的次数
- `avoidable_nonprimary_language_term_count`：本可自然写成文稿主语言，却保留为其他语言短语的次数
- `translationese_phrase_count`：在英文文稿里，明显带翻译腔或不自然英语表达的次数
- `register_shift_count`：语体突然漂移，导致段落声音不稳定的次数
- `inflated_significance_count`：把普通判断包装成重大意义或历史转折的次数
- `promotional_language_count`：像广告、演讲稿或泛化品牌文案的句子数量
- `vague_attribution_count`：没有责任主体的模糊归因数量
- `formulaic_section_count`：模板化小标题或模板化段落推进的数量
- `ai_vocabulary_or_synonym_cycling_count`：用过于“聪明”的词或反复换词来制造写作感的次数
- `copula_avoidance_count`：本可直接判断，却故意绕开简单系动词结构的次数
- `rule_of_three_or_negative_parallelism_count`：刻意工整三连句或 `not X, not Y, but Z` 的过度使用次数
- `formatting_artifact_count`：过多 em dash、bold、title case、小标题碎片化等格式性痕迹
- `chatbot_residue_count`：明显 chatbot/assistant 残留的次数
- `generic_uplift_ending_count`：结尾情绪正确但没有新增判断的次数
- `defensive_disclaimer_count`：防御性澄清、边界管理或免责声明腔的次数
- `overexplained_chain_count`：本可直接下判断，却被写成完整说明链或标准答题结构的次数
- `negative_parallelism_count`：`不是 A，而是 B`、`既不是 A，也不是 B`、`不是因为 A，而是因为 B` 这类否定式对举的次数
- `former_latter_count`：`前者 / 后者` 这类抽象对举承接的次数
- `mechanical_enumeration_count`：`第一 / 第二 / 第三` 或同强度的工整编号并列出现的次数
- `template_paragraph_rhythm_count`：段落反复出现“定义 / 展开 / 回收”固定节奏的次数
- `choppy_short_sentence_count`：本可自然连写，却被切成多句过短短句的次数
- `abstract_noun_cluster_count`：抽象名词密集堆叠，导致句子像概念压缩而非自然表达的次数
- `redundant_paragraph_count`：表达重复、功能重叠的段落数量

这些计数应服务于判断，不应反过来绑架判断。比如 `concrete_evidence_count` 很高，不代表文章一定好；堆砌引用和数字同样可以写出糟糕文章。

如果 `editing_goal = humanizer`，也不要把“更不像 AI”误当成自动加分项。真正有价值的版本，应该同时满足：

- 更少 AI 痕迹
- 仍然保住原意
- 仍然保住具体性
- 仍然保住作者声音

## 5. Keep / Discard Rules

为了适配 `autoresearch` 风格的反馈实验，建议不要只看“这篇稿子绝对分数高不高”，而要看“这次修改是否让稿子在关键维度上真实变好”。

在 `autoresearch-blog:N` 交互里，除了比较新旧版本，也要始终和本次任务的 `target_score_percent` 对齐。每次任务开始前，这个 target 都应被显式确认。

### 5.1 Keep

满足以下条件之一，且没有 `hard gate`：

- `overall_score` 提升 `>= 3`
- `overall_score` 提升 `>= 1.5`，并且提升来自高权重维度：
  - `Insight Density and Originality`
  - `Evidence, Accuracy, and Epistemic Honesty`
  - `Audience Fit and Thesis Clarity`
- 总分近乎持平，但代码式“简化收益”明显：
  - 更短
  - 更清楚
  - 更少废话
  - 不牺牲核心证据和洞见

### 5.2 Discard

默认 `discard` 的情况：

- 命中任何 `hard gate`
- `overall_score` 下降
- 分数提升主要来自低权重表面优化，比如更花哨的句式，但核心判断没有变强
- 可读性略升，但洞见密度、证据质量或论点清晰度下降
- 文章变长很多，但新增信息密度不足
- 在 `humanizer` 目标下，虽然更不像 AI 了，但也明显更空、更假口语化、或更不像原作者
- 在 `humanizer` 或中文技术文章场景下，虽然局部更顺，但明显保留了高频模板句式或节奏：
  - 否定式对举仍然反复出现
  - `前者 / 后者` 和机械三段并列仍然过密
  - 段落还在反复使用“定义 / 展开 / 回收”的固定节奏
  - 通过切碎短句来伪造力度
  - 抽象名词堆叠依然让句子像模型压缩出来的说明文字

这里要明确区分：

- `discard`：本轮候选版本不采纳
- `stop`：整个实验停止

在 `autoresearch-blog:N` 或 `autoresearch-blog:continue:N` 里，分数下降的轮次应被允许出现，但必须被 `discard`。只要还没达到 target，且预算还没用完，就应继续后续轮次，而不是因为一次下降就提前停掉整个实验。

### 5.3 Tie-break

如果两版总分接近，优先保留：

1. 论点更清楚的版本
2. 证据更扎实的版本
3. 更短但不损失信息的版本
4. 更像作者本人、而不是更像通用 AI 写作模板的版本

## 6. Suggested Output Format

建议 judge 输出机器可读结果，方便后续做日志、对比和自动迭代。

```json
{
  "verdict": "keep",
  "iteration": 2,
  "max_iterations": 5,
  "overall_score": 84.5,
  "target_score_percent": 85.0,
  "progress_percent": 99.4,
  "score_gap_to_target": 0.5,
  "target_met": false,
  "discard_count": 1,
  "hard_fail": false,
  "hard_fail_reasons": [],
  "dimension_scores": {
    "audience_fit_and_thesis_clarity": 4.5,
    "insight_density_and_originality": 4.0,
    "evidence_accuracy_and_epistemic_honesty": 4.0,
    "structure_and_narrative_flow": 4.0,
    "clarity_readability_and_compression": 4.0,
    "actionability_or_transferable_takeaways": 4.0,
    "voice_and_memorability": 4.5,
    "title_opening_and_ending_quality": 4.0
  },
  "diagnostics": {
    "unsupported_claim_count": 0,
    "concrete_evidence_count": 6,
    "original_insight_count": 4,
    "actionable_takeaway_count": 3,
    "filler_sentence_count": 2,
    "jargon_without_explanation_count": 1,
    "redundant_paragraph_count": 1
  },
  "strengths": [
    "Makes a sharp distinction between session trace and environmental evidence",
    "Uses concrete OpenClaw observations instead of generic claims"
  ],
  "must_fix": [
    "Tighten the transition into the cost section",
    "Add one sentence clarifying the experiment boundary"
  ],
  "summary": "The article has a clear argument and credible evidence. The main remaining issue is compression in the middle sections.",
  "keep_reason": "Meaningful gain in clarity without losing insight density"
}
```

其中：

- `target_score_percent`：本次任务开始前由用户确认的目标分数
- `progress_percent`：`min(overall_score / target_score_percent * 100, 100)`
- `score_gap_to_target`：`max(target_score_percent - overall_score, 0)`
- `target_met`：当前版本是否已达到目标

当文章面向的不是纯专家读者时，judge 在 `clarity_readability_and_compression` 上应特别检查：

- 是否把术语列表改写成了类别
- 是否给了足够少但足够具体的例子
- 读者是否能不靠背景知识就看懂这些术语为什么被放在一起
- 标点是否在帮助读者分层理解，而不是让句子变得更碎或更拧
- 除必要术语外，语言是否仍然以自然主语言为主，而不是混入不必要的异语表达

如果是在迭代过程中向用户汇报，建议同时给一句简短进度提示，例如：

```text
Iteration 2/5 | score 84.5 | target 85.0 | progress 99.4% | verdict keep
```

## 7. Anti-Goodhart Reminder

这个 judge 最容易被滥用的地方有三个：

- 把“可读”误当成“有价值”
- 把“像成熟 blog”误当成“有作者洞见”
- 把“加更多例子和数据”误当成“证据更扎实”

所以 judge 必须始终优先看三件事：

1. 有没有明确判断
2. 这个判断是否被真实支撑
3. 读者读完是否真的获得了新的认知结构

如果这三件事不成立，再漂亮的 prose 也不应高分。

同理，再密集的专业名词也不等于更专业。对多数 blog 来说，把术语压成可理解的结构，通常比把术语堆得更满更有价值。

## 8. What Bad Looks Like

下面这些情况，即使表面上写得顺，也应被明显扣分：

- 正确但平庸：没有错，但没有新的东西
- 聪明但虚：概念很漂亮，证据很弱
- 丰满但稀：篇幅很长，信息密度很低
- 尖锐但失真：判断很强，但靠夸张推动
- 像人类写作，但不像这个作者写作

## 9. Current Recommendation

对于 `autoresearch-blog`，建议先把这份 judge 当作 `technical insight essay` 的默认 rubric 使用。等你后面开始覆盖 tutorial、announcement、case study、review 这几类文章，再分别拆出不同权重版本。
