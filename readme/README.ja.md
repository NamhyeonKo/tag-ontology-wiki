<h1 align="center">TOW — Tag Ontology for Wiki</h1>

<p align="center">
  <a href="https://github.com/NamhyeonKo/tag-ontology-wiki/stargazers"><img alt="stars" src="https://img.shields.io/github/stars/NamhyeonKo/tag-ontology-wiki?label=stars"></a>
  <a href="https://github.com/NamhyeonKo/tag-ontology-wiki/releases/latest"><img alt="release" src="https://img.shields.io/github/v/release/NamhyeonKo/tag-ontology-wiki?label=release"></a>
  <a href="../LICENSE"><img alt="license" src="https://img.shields.io/github/license/NamhyeonKo/tag-ontology-wiki?label=license"></a>
</p>

<p align="center"><a href="../README.md">English</a> · <a href="README.ko.md">한국어</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.zh-TW.md">繁體中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.es.md">Español</a> · <a href="README.fr.md">Français</a></p>

Obsidian vault と開発プロジェクトを接続するエージェントスキルプラグインです。両方を概念で検索し、プロジェクトの `.tow/` メタデータで文書にタグを付け、選択した内容を新しい vault ノートとして送信します。プロジェクト文書は変更せず、vault の保守作業では内容を保持します。Claude Code、Codex、Google Antigravity で動作します。

> **バージョン:** 0.5.9。

## 概要

通常のメンテナンスでは、文章、数式・コードの内容、表の値を保持し、選択したフロントマターと書式だけを変更します。任意の後処理は、ユーザー自身のテンプレートと明示的に選択した操作に従います。TOW は、フロントマターのないノートを含め、既存の vault 構成で動作します。任意で採用できるタグ優先の LLM Wiki レシピには、それぞれ独立して選択できる 3 つの層があります。

- **PARA フォルダー**: Projects、Areas、Resources、Archives。
- フロントマターの**分類フィールド**: `category`、`type`、`status`、`kind`。
- **概念タグのオントロジー**: エイリアスと上位・下位関係を持つタグ辞書。

セットアップ時に PARA を選択することも、独自のフォルダーを維持することもできます。通常の検索や本文の操作に、辞書やメタデータの整理は必要ありません。クエリでは1回の `tow search` でタグ辞書の概念、タイトル、見出し、本文、プロパティを AND・OR・NOT で組み合わせて検索し、回答で説明するノートだけを開きます。利用可能なプロパティがあれば検索精度が向上します。規約の全体は [docs/methodology.md](../docs/methodology.md) にあります。

TOW は、ローカルのエージェントホストに 12 のワークフローをインストールします。vault 専用のワークフローは Obsidian ノートを管理します。プロジェクトでは `tow-query` が接続済み vault と現在のプロジェクトを検索し、`tow-send-vault` が承認後に選択した内容を新しい vault ノートとして作成します。プロジェクトのタグとハッシュは `.tow/` メタデータに保存し、プロジェクト文書は変更しません。

パッケージには、スキル、共通規約、Python ヘルパー [`scripts/tow.py`](../scripts/tow.py) が含まれます。このヘルパーは分類ルールを検査し、ノートの解析、タグ検索、辞書の検証・変更のために [`tag-ontology`](https://github.com/NamhyeonKo/obsidian-tag-ontology) npm CLI を呼び出します。モデルとファイル操作ツールは、エージェントのホストが提供します。

TOW は Tag Ontology CLI を使ってタグを検索し、辞書を検証・管理します。[Obsidian 用 Tag Ontology プラグイン](https://github.com/NamhyeonKo/obsidian-tag-ontology)（[コミュニティプラグインページ](https://community.obsidian.md/plugins/tag-ontology)）を TOW と併用すると、管理しているタグの階層や関係をグラフで視覚的に探索できます。

```text
tag-ontology@0.3.1        辞書の検査、検索、編集、ノートの解析
      ▲  npx tag-ontology … --json
tow (this plugin)         vault 規約の検査、スキル
      ▲  Claude Code / Codex / Antigravity
ユーザーの Obsidian vault
```

## スキル

| スキル | 使用する場面 | 変更内容 |
| --- | --- | --- |
| `tow-setup` | vault の設定、プロジェクト用の接続、プロジェクトメタデータの登録 | 名前を先に確認し、承認された `.tow/` メタデータまたは個人接続設定のみを書き込む |
| `tow-send-vault` | 選択したプロジェクト内容を接続先の vault に送る | 承認後に新しいノートを作成。変換の依頼がなければ選択した本文を保持 |
| `tow-query` | 自然言語の条件、カスタムプロパティ、タグ、テキストでドキュメントを探す | 読み取り専用。1回の `tow search` クエリ（AND、OR、NOT）で概念、タイトル、本文、フィールドを検索。一致項目を一覧表示し、回答で説明するノートだけを開きます |
| `tow-check` | フロントマター、Markdown、数式、コード、表、参照を検査する | まず報告。選択した構文修正でも、文章、データ本体、値を保持 |
| `tow-tag-suggest` | 選択したノートの概念タグを提案する | ユーザーが選択した追加・削除のみを適用 |
| `tow-tag-sync` | 新しいタグの登録、エイリアスの解決、辞書の整合を行う | まず提案し、承認された辞書・タグの変更を適用 |
| `tow-classify` | カテゴリーの登録、ノートの再分類、旧式フィールドの変換を行う | 項目と変換を承認。既存ノートへの遡及的な変更は別途選択 |
| `tow-link` | 既存のタイトル・エイリアスの言及をリンクにする | 承認された初出箇所のみ。表示される語句を保持 |
| `tow-edit` | ユーザーのテンプレート・ルールに沿って、明示的に本文を後処理する | 選択した新規・空欄の内容、または変換のみ。ルールが不足していれば質問 |
| `tow-merge` | 選択した統合先・ルールに沿って、明示的に統合する | 既定では原文のまま転記。ケースごとの選択と、破棄に対する別途確認 |
| `tow-review` | ユーザーのルールに照らしてノートを確認し、後処理を提案する | 具体的な後続操作が選択されるまで読み取り専用 |
| `tow-ingest` | 選択したルールに沿って、明示的に格納・ソースの後処理を行う | 既定では原文のまま格納。メタデータの付与、派生ノートの作成、書き換えを暗黙には行わない |

3 つのホストはすべて、これらのスキル、規約、CLI を共有します。Claude Code では `/tow:tow-query` を呼び出し、Codex では `$` または `/skills` で `tow-query` を選択し、Antigravity では `/tow-query` を呼び出します。

## 内容の保持と任意の後処理

メタデータのみの変更では、独立したスナップショットと `tow verify-body` を使って、本文のバイト列が完全に一致することを確認します。書式には Markdown 構文、数式の区切り、コードフェンス・言語に応じた書式、表が含まれますが、その内容は変更しません。曖昧な修正や検証できない修正は、報告に留めます。これはスキルの指示と限定的なバイト比較の組み合わせであり、汎用的な意味検証器や、ホストが強制するセキュリティフックではありません。

`tow-edit`、`tow-merge`、`tow-ingest`、`tow-review` は名称を維持し、任意の後処理ワークフローとして利用できます。ユーザーが提供した、または確立済みのテンプレートとルールを再利用します。一般的な整理の依頼やテンプレートだけでは、記入済みの文章の書き換え、ハブの生成、ノートの分割は許可されません。[内容の保持](../docs/preservation.md)と[後処理](../docs/post-curation.md)を参照してください。

## 必要な環境

- プラグインをサポートする Claude Code、Codex、または Google Antigravity
- GitHub からのインストールに使用する Git
- 任意の `tag-ontology` 解析・オントロジー機能を使う場合は、Node.js 22.18 以降と、`PATH` 上の npm/npx
- Obsidian CLI は任意。ネイティブ検索には、CLI が有効で、実行中のアプリから対象 vault にアクセスできることが必要。CLI がなくてもファイル検索は利用可能
- Python 3.10 以降（標準ライブラリのみ）

スキルは指定された範囲の vault ファイルを読み取り、承認された変更のみを適用します。開いたノートの内容は、エージェントのホストが自身のモデルとプライバシー設定に従って処理します。TOW にホスト型バックエンドはありません。npm が固定バージョンの CLI をダウンロードし、ファイルへのアクセスはホストが制御します。

## GitHub からのインストール

この公開リポジトリから直接インストールします。公式ディレクトリへの登録は任意です。以下のコマンドは `main` を使用します。インストール後はホストの新しいセッションを開始してください。検証、vault 設定、更新については、[インストールとトラブルシューティングのガイド](../docs/installation.md)を参照してください。

### Claude Code

```text
/plugin install tow --marketplace NamhyeonKo/tag-ontology-wiki
```

Claude Code 2.1.275 より前のバージョンでは、次を使用します。

```text
/plugin marketplace add NamhyeonKo/tag-ontology-wiki
/plugin install tow@tag-ontology-wiki
```

### Codex

シェルで実行します。

```bash
codex plugin marketplace add NamhyeonKo/tag-ontology-wiki --ref main
codex plugin add tow@tag-ontology-wiki
```

### Antigravity

シェルで実行し、その後 Antigravity の新しいセッションを開始します。

```bash
agy plugin install https://github.com/NamhyeonKo/tag-ontology-wiki
```

## 更新

使用するホストのコマンドをターミナルで実行し、新しいセッションを開始します。

**Claude Code:**

```bash
claude plugin update tow@tag-ontology-wiki
```

**Codex:**

```bash
codex plugin marketplace upgrade tag-ontology-wiki
codex plugin add tow@tag-ontology-wiki
```

**Antigravity:** 同じソースから再インストールします。

```bash
agy plugin install https://github.com/NamhyeonKo/tag-ontology-wiki
```

ホストのプラグイン一覧・詳細コマンドで、インストール済みのバージョンを確認してください。ホストごとの動作と確認方法は、[更新とトラブルシューティング](../docs/installation.md#update)を参照してください。

## 初めて使う

vault の保守だけを行う場合は、vault をホストのワークスペースとして開きます。vault 側の TOW ファイルは可視の `tow/` に置き、外部プロジェクトのメタデータは引き続きプロジェクト `.tow/` に置きます。プロジェクトで使う場合は、プロジェクトのワークスペースを開き、`tow-setup` を選択して vault を接続し、プロジェクトメタデータを登録します。新しいプロジェクトセッションで `tow-query` を選択し、次のように依頼します。

```text
私の vault は /absolute/path/to/vault です。カテゴリーまたは概念で、RAG に関する
プロジェクトノートを探し、置き換え済みの文書は除外してください。現在のプロジェクトと
接続済み vault の両方を検索し、一致するノートを読んでから要約して、出典・パス・一致理由・件数を返してください。ファイルは変更しないでください。
```

プロジェクト登録や辞書なしでも検索できます。プロジェクトへのタグ付けには `.tow/` メタデータが必要です。個人接続は `$TOW_VAULT` または `~/.tow/config.json` に保存され、プロジェクトファイルには記録されません。現在のディレクトリが vault 内にある場合、その vault が個人接続より優先されます。明示的に選ぶには `--root` を使います。vault 内での検索はその vault のみを対象にします。vault を整理するには `tow-setup` を選択してください。PARA の採用を確認し、既存の構成・スキーマを保持します。新しい vault 設定は `tow/config.json` に置かれ、従来の `.tow/` および 0.4.x vault も `tow/` に移行するまでは読み取れます。移行では従来の Markdown ルール文書を `tow/tags.md` / `tow/categories.md` に取り込み、元ファイルを削除した後はそれらへのノートリンクを更新してください。[セットアップガイド](../docs/installation.md#configure-the-vault)と[プロジェクト接続手順](../docs/installation.md#connect-a-vault-to-a-project)を参照してください。

## CLI とセットアップの確認

ヘルパーは `npx --yes tag-ontology@0.3.1` を使用します。必要に応じて npm がその正確なバージョンを取得します。ヘルパーを手動で実行するときは、インストールされた `scripts/tow.py` のパスを使います。規約中の `tow` は、そのパスの略記です。

TOW 0.5.9 にも `tag-ontology` 0.3.1 にも、`doctor` コマンドはありません。まず次を実行してください。

```bash
python3 --version
node --version
npx --yes tag-ontology@0.3.1 --version
```

TOW の `lint` は、採用した TOW メタデータだけを対象に実行してください。辞書の検査は、初期化済みのオントロジー機能だけに適用されます。任意のメタデータや辞書がなくても、インストールの失敗ではありません。続いて[セットアップの確認](../docs/installation.md#check-the-setup)に従い、インストール済みのプラグイン、設定、辞書、ノートのタグを検証してください。`lint` は分類フィールドとタグ数を対象とし、check スキルはノートごとの書式・参照の確認を追加します。lint の結果に問題がないだけでは、すべてのスキル検査を網羅したことにはなりません。

## ドキュメント

- [インストール、vault 設定、トラブルシューティング](../docs/installation.md)
- [vault の規約とヘルパーコマンド](../docs/methodology.md)
- [内容の保持](../docs/preservation.md)と[任意の後処理](../docs/post-curation.md)
- [評価と検証の限界](../docs/evaluation.md)

詳細ガイドは英語で管理され、すべての言語版 README で共有しています。

## コントリビューション

バグ報告、対象を絞った修正、ドキュメントの改善、翻訳の訂正を歓迎します。開発環境のセットアップ、検査、スキル参照資料と読者向け翻訳の区別については、[CONTRIBUTING.md](../CONTRIBUTING.md)をお読みください。バグの報告や機能の提案には、[Issue フォーム](https://github.com/NamhyeonKo/tag-ontology-wiki/issues/new/choose)をご利用ください。

## サポート

TOW は無料のオープンソースです。時間の節約に役立った場合は、[コーヒーで応援](https://buymeacoffee.com/namhyunko)していただけます。

## ライセンス

[MIT](../LICENSE)
