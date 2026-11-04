# TOW — Tag Ontology for Wiki

用于管理 **Obsidian vault 内部文档**的智能体技能插件：搜索笔记、管理 frontmatter，并在保留内容的前提下修正格式。将 vault 作为工作区，可在 Claude Code、Codex 和 Google Antigravity 中使用。

[English](../README.md) · [한국어](README.ko.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Français](README.fr.md)

> **版本：** 0.4.2。

## 概述

常规维护保留原有文字、数学公式和代码的内容以及表格值，仅修改选定的 frontmatter 和格式。可选的后续整理遵循你自己的模板和明确选择的操作。TOW 支持现有 vault 目录结构，也支持没有 frontmatter 的笔记。其可选的标签优先 LLM Wiki 方案包含三个可独立选择的层次：

- **PARA 文件夹**：Projects、Areas、Resources、Archives。
- frontmatter 中的**分类字段**：`category`、`type`、`status`、`kind`。
- **概念标签本体**：包含别名及上下位关系的标签词典。

设置时可选择 PARA，也可保留自己的文件夹。普通搜索和正文操作不要求使用词典或先清理元数据。查询优先使用 Obsidian CLI，必要时补充限定范围的文件搜索，最后验证内容；现有属性可提高查询精度。完整约定见 [docs/methodology.md](../docs/methodology.md)。

TOW 为本地编程智能体安装十一项工作流程。指定 vault 和笔记后，智能体读取相关文件，按分类和概念标签搜索，并提出范围明确的修改方案供你批准。文件仍保存在你的 Obsidian vault 中。

插件包含技能、共享约定和 Python 辅助脚本 [`scripts/tow.py`](../scripts/tow.py)。该脚本检查分类规则，并调用 [`tag-ontology`](https://github.com/NamhyeonKo/obsidian-tag-ontology) npm CLI 来解析笔记、查询标签及验证或修改词典。模型和文件工具由智能体宿主提供。

TOW 使用 Tag Ontology CLI 查询标签并验证、管理词典。同时安装 [Obsidian 的 Tag Ontology 插件](https://github.com/NamhyeonKo/obsidian-tag-ontology)（[社区插件页面](https://community.obsidian.md/plugins/tag-ontology)），即可通过图谱直观查看所管理标签的层级和关系。

```text
tag-ontology@0.1.3        词典检查、查询、编辑和笔记解析
      ▲  npx tag-ontology … --json
tow（本插件）             vault 约定检查、技能
      ▲  Claude Code / Codex / Antigravity
你的 Obsidian vault
```

## 技能

| 技能 | 适用场景 | 修改范围 |
| --- | --- | --- |
| `tow-setup` | 选择 PARA 或现有结构；按需启用词典 | 仅列出顶层文件夹；经批准后创建文件夹、词典和 `tow.json`，不移动笔记 |
| `tow-query` | 按自然语言条件、自定义属性、标签或文本查找文档 | 只读；优先使用 CLI，必要时使用限定范围的文件搜索，并区分已验证的匹配与推断候选 |
| `tow-check` | 检查 frontmatter、Markdown、数学公式、代码、表格和引用 | 先报告；选定的语法修正保留文字、内部内容和值 |
| `tow-tag-suggest` | 为选定笔记推荐概念标签 | 仅应用你选定的添加或移除操作 |
| `tow-tag-sync` | 注册新标签、处理别名或协调词典 | 先提出方案；仅应用已批准的词典或标签修改 |
| `tow-classify` | 注册分类、重新分类笔记或转换旧字段 | 分类条目和转换需批准；是否追溯修改已有笔记另行选择 |
| `tow-link` | 为已有的标题或别名提及添加链接 | 仅链接已批准的首次提及；保留显示文字 |
| `tow-edit` | 按你的模板或规则明确选择正文整理 | 仅处理选定的新内容、空白章节或转换；缺少规则时先询问 |
| `tow-merge` | 按选定的目标位置和规则明确合并 | 默认逐字转移；逐项选择，丢弃内容需单独确认 |
| `tow-review` | 按你的规则审查笔记并提出后续整理建议 | 选定具体后续操作前保持只读 |
| `tow-ingest` | 按你选定的规则归档文件或整理来源笔记 | 默认原样归档；不隐含添加元数据、派生内容或重写 |

三个宿主共享这些技能、约定和 CLI。在 Claude Code 中调用 `/tow:tow-query`；在 Codex 中通过 `$` 或 `/skills` 选择 `tow-query`；在 Antigravity 中调用 `/tow-query`。

## 内容保留与可选的后续整理

仅修改元数据时，使用独立快照和 `tow verify-body` 验证正文的字节完全一致。格式修正涉及 Markdown 语法、公式分隔符、代码围栏、对应语言的代码格式和表格，但不改变内部内容。含义不明确或无法验证的修正仅作报告。这些机制由技能指令和范围有限的字节比较组成，并非通用语义验证器，也不是由宿主强制执行的安全钩子。

`tow-edit`、`tow-merge`、`tow-ingest` 和 `tow-review` 保留现有名称，作为可选的后续整理流程。它们复用你提供或既定的模板和规则；一般清理请求或仅提供模板，并不授权重写已有正文、生成中心笔记或拆分笔记。参见[内容保留](../docs/preservation.md)和[后续整理](../docs/post-curation.md)。

## 环境要求

- 支持插件的 Claude Code、Codex 或 Google Antigravity
- 从 GitHub 安装时需要 Git
- 使用可选的 `tag-ontology` 解析或本体功能时，需要 Node.js 22.18 或更高版本，且 npm/npx 在 `PATH` 中
- Obsidian CLI 为可选项；原生搜索要求启用 CLI，且运行中的应用可访问目标 vault。没有 CLI 时仍可使用文件搜索
- Python 3.10 或更高版本（仅使用标准库）

技能读取你限定范围内的 vault 文件，并仅应用你批准的修改。智能体宿主根据自身的模型和隐私设置处理打开的笔记内容。TOW 没有托管后端；npm 下载固定版本的 CLI，文件访问由宿主管理。

## 从 GitHub 安装

直接从此公开仓库安装，无需先提交至官方目录。以下命令使用 `main`；安装后请启动新的宿主会话。安装验证、vault 设置和更新方法见[安装与故障排查指南](../docs/installation.md)。

### Claude Code

```text
/plugin install tow --marketplace NamhyeonKo/tag-ontology-wiki
```

Claude Code 低于 2.1.275 时：

```text
/plugin marketplace add NamhyeonKo/tag-ontology-wiki
/plugin install tow@tag-ontology-wiki
```

### Codex

在终端中运行：

```bash
codex plugin marketplace add NamhyeonKo/tag-ontology-wiki --ref main
codex plugin add tow@tag-ontology-wiki
```

### Antigravity

在终端中运行，然后启动新的 Antigravity 会话：

```bash
agy plugin install https://github.com/NamhyeonKo/tag-ontology-wiki
```

## 更新

在终端中运行对应宿主的命令，然后启动新会话。

**Claude Code：**

```bash
claude plugin update tow@tag-ontology-wiki
```

**Codex：**

```bash
codex plugin marketplace upgrade tag-ontology-wiki
codex plugin add tow@tag-ontology-wiki
```

**Antigravity：** 从同一来源重新安装。

```bash
agy plugin install https://github.com/NamhyeonKo/tag-ontology-wiki
```

使用宿主的插件列表或详情命令确认已安装版本。宿主特有的行为和检查步骤见[更新与故障排查](../docs/installation.md#update)。

## 首次使用

将 vault 作为宿主工作区打开。在新会话中按上述宿主对应的方法选择 `tow-query`，然后发送：

```text
我的 vault 位于 /absolute/path/to/vault。按 category 或概念查找与 RAG 相关的项目笔记，
排除已被替代的文档。总结前先读取匹配的笔记，并返回路径和数量。不要修改文件。
```

无需设置即可开始搜索。如需可选的组织功能，请选择 `tow-setup`；它会先询问你是否使用 PARA，并保留现有结构和字段模式。TOW 读取 vault 根目录的 `tow.json`；省略的设置采用[设置指南](../docs/installation.md#configure-the-vault)中的默认值。安装不会创建或迁移 vault。

## CLI 与设置检查

辅助脚本使用 `npx --yes tag-ontology@0.1.3`；npm 在需要时下载该确切版本。手动运行辅助命令时，使用已安装的 `scripts/tow.py` 路径。约定中的 `tow` 是该路径的简写。

TOW 0.4.2 和 `tag-ontology` 0.1.3 均没有 `doctor` 命令。先运行：

```bash
python3 --version
node --version
npx --yes tag-ontology@0.1.3 --version
```

仅对采用 TOW 元数据的笔记运行 TOW `lint`；词典检查仅适用于已初始化的本体功能。缺少未选用的可选元数据或词典，并不表示安装失败。然后按[设置检查](../docs/installation.md#check-the-setup)验证插件、配置、词典和笔记标签。`lint` 检查分类字段和标签数量，检查技能还逐篇检查格式与引用。仅有 lint 通过并不代表完成了技能的全部检查。

## 文档

- [安装、vault 设置与故障排查](../docs/installation.md)
- [vault 约定与辅助命令](../docs/methodology.md)
- [内容保留](../docs/preservation.md)与[可选的后续整理](../docs/post-curation.md)
- [评估与验证限制](../docs/evaluation.md)

详细指南以英文维护，各语言 README 共享同一套文档。

## 参与贡献

欢迎提交问题报告、范围明确的修复、文档改进和翻译校正。开发环境、检查步骤以及技能引用文档与读者用译文的区别，见 [CONTRIBUTING.md](../CONTRIBUTING.md)。报告问题或建议功能时，请使用 [Issue 表单](https://github.com/NamhyeonKo/tag-ontology-wiki/issues/new/choose)。

## 支持

TOW 是免费的开源项目。如果它为你节省了时间，欢迎[请我喝杯咖啡](https://buymeacoffee.com/namhyunko)。

## 许可证

[MIT](../LICENSE)
