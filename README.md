# autoresearch-blog

`autoresearch-blog` 是一个用来迭代优化单篇 blog 的 skill，当前支持中文和英文文稿。

它不是一次性润色 prompt，而是一个小型反馈实验：

- 先确认目标分数
- 在固定预算内迭代
- 每轮判断 `keep` 或 `discard`
- 支持之后继续实验

## 适用场景

- 技术分析文
- 观点型 blog
- 想比较多轮修改效果的长文
- 想通过 judge 迭代减少 AI 写作痕迹的 humanizer 场景

支持语言：

- 中文
- 英文

## 调用方式

新建实验：

```text
autoresearch-blog
autoresearch-blog:3
autoresearch-blog:5
```

继续实验：

```text
autoresearch-blog:continue
autoresearch-blog:continue:3
autoresearch-blog:continue:5@100
```

含义：

- `N` 表示这次最多迭代多少轮
- `@TARGET` 表示把目标分数改成新的目标

## 怎么加到 agent 里

这个 skill 本质上就是一个带 `SKILL.md` 的目录。

最小需要这些文件：

```text
autoresearch-blog/
  SKILL.md
  judge.md
  scripts/
    render_experiment_progress.py
```

### 加到 Codex

把整个目录放到 Codex 的 skills 目录下即可，例如：

```bash
mkdir -p ~/.codex/skills
cp -R /path/to/autoresearch-blog ~/.codex/skills/autoresearch-blog
```

然后在会话里直接用：

```text
autoresearch-blog:3
```

### 加到 Claude Code 类 agent

如果你的 Claude Code 或同类 agent 使用本地 skills 目录，也可以用同样的方式接入：

```bash
mkdir -p ~/.claude/skills
cp -R /path/to/autoresearch-blog ~/.claude/skills/autoresearch-blog
```

核心要求只有一个：

- agent 能读到这个目录里的 `SKILL.md`

如果你的 agent 不是用固定目录，而是支持“从本地路径加载 skill”，那就直接把这个目录指给它。

### 给用户分发时需要带哪些文件

如果你要把这个 skill 发给别人，至少带上：

- `SKILL.md`
- `judge.md`
- `scripts/render_experiment_progress.py`

`README.md` 只是说明文档，不是 skill 运行必需文件。

## 运行方式

开始前会先确认：

- 目标分数
- 最大迭代次数
- 文稿语言
- 本次主要目标是 `insight_blog` 还是 `humanizer`

然后每轮会：

1. 读取当前 best 版本
2. 只修改少数高杠杆问题
3. 重新评分
4. 决定 `keep` 或 `discard`
5. 汇报当前进度

停止条件只有两个：

- 达到目标分数
- 用完本次预算

## 输出内容

每次实验会保存：

- 当前实验状态
- 每轮结果日志
- 被保留版本的快照
- 一张进度图

默认目录：

```text
.autoresearch-blog/
```

## 例子

```text
autoresearch-blog:3
目标 85 分
```

继续并提高目标：

```text
autoresearch-blog:continue:5@100
```

## 说明

- 对外用法看这个文件就够了
- 评分细则见 `judge.md`
- 内部协议见 `SKILL.md`
