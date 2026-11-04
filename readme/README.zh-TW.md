# TOW — Tag Ontology for Wiki

用於管理 **Obsidian vault 內部**文件的代理技能外掛程式：搜尋筆記、管理 frontmatter，並在保留內容的前提下修正格式。以 vault 為工作區，可在 Claude Code、Codex 和 Google Antigravity 中執行。

[English](../README.md) · [한국어](README.ko.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Français](README.fr.md)

> **版本：** 0.4.2。

## 概覽

一般維護會保留文字、數學公式與程式碼的內容，以及表格中的值；只變更所選的 frontmatter 和格式。選用的後續整理會遵循你自己的範本，以及明確選擇的操作。TOW 適用於現有的 vault 結構，包括沒有 frontmatter 的筆記。其選用的標籤優先 LLM Wiki 方案包含三個可獨立選擇的層次：

- **PARA 資料夾**：Projects、Areas、Resources、Archives。
- frontmatter 中的**分類欄位**：`category`、`type`、`status`、`kind`。
- **概念標籤本體**：具有別名及上位／下位關係的標籤字典。

設定時可選擇 PARA，也可保留自己的資料夾。一般搜尋及內文操作不需要字典，也不需要清理中繼資料。查詢會先使用 Obsidian CLI，必要時進行限定範圍的檔案搜尋，最後驗證內容；可用的屬性能提高查詢精確度。完整慣例請見 [docs/methodology.md](../docs/methodology.md)。

TOW 會將十一個工作流程安裝至本機的程式開發代理。你指定 vault 和筆記後，代理會讀取相關檔案、搜尋分類及概念標籤，並提出限定範圍的變更供你核准。檔案仍保留在你的 Obsidian vault 中。

套件包含技能、共用慣例，以及 Python 輔助程式 [`scripts/tow.py`](../scripts/tow.py)。該輔助程式會檢查分類規則，並呼叫 [`tag-ontology`](https://github.com/NamhyeonKo/obsidian-tag-ontology) npm CLI，以解析筆記、查詢標籤，以及驗證／變更字典。模型及檔案工具由你的代理宿主提供。

TOW 使用 Tag Ontology CLI 查詢標籤，以及驗證／管理字典。搭配安裝 [Obsidian 的 Tag Ontology 外掛程式](https://github.com/NamhyeonKo/obsidian-tag-ontology)（[社群外掛程式頁面](https://community.obsidian.md/plugins/tag-ontology)），即可透過圖形視覺化探索你所管理的標籤階層及關係。

```text
tag-ontology@0.1.3        字典檢查、查詢、編輯、筆記解析
      ▲  npx tag-ontology … --json
tow (this plugin)         vault 慣例檢查、技能
      ▲  Claude Code / Codex / Antigravity
你的 Obsidian vault
```

## 技能

| 技能 | 使用時機 | 變更 |
| --- | --- | --- |
| `tow-setup` | 選擇 PARA 或現有結構；可選擇啟用字典 | 只列出頂層資料夾；核准後才建立資料夾、字典及 `tow.json`，絕不移動筆記 |
| `tow-query` | 以自然語言條件、自訂屬性、標籤或文字尋找文件 | 唯讀；優先使用 CLI，必要時改用限定範圍的檔案搜尋；驗證符合項目，並將推論候選項目分開列出 |
| `tow-check` | 檢查 frontmatter、Markdown、數學公式、程式碼、表格及參照 | 先回報；所選的語法修正會保留文字、資料本體及值 |
| `tow-tag-suggest` | 為所選筆記推薦概念標籤 | 只套用你選擇的新增／移除項目 |
| `tow-tag-sync` | 登記新標籤、處理別名，或調整字典使其一致 | 先提出建議；套用核准的字典／標籤變更 |
| `tow-classify` | 登記類別、重新分類筆記、轉換舊版欄位 | 核准項目及轉換；回溯變更須另行選擇 |
| `tow-link` | 為既有的標題／別名提及處加上連結 | 只處理已核准的首次提及處；保留顯示文字 |
| `tow-edit` | 明確依照你的範本／規則進行內文後續整理 | 僅限所選的新內容／空白內容或轉換；缺少規則時會詢問 |
| `tow-merge` | 明確依照所選目的地／規則整合內容 | 預設逐字轉移；逐案選擇，且另行確認捨棄內容 |
| `tow-review` | 依照你的規則檢視筆記並提出後續整理建議 | 在選定具體的後續操作之前維持唯讀 |
| `tow-ingest` | 明確依照你選擇的規則歸檔／進行來源後續整理 | 預設逐字歸檔；不隱含授權新增中繼資料、衍生內容或改寫 |

三種宿主共用這些技能、慣例及 CLI。在 Claude Code 中呼叫 `/tow:tow-query`；在 Codex 中使用 `$` 或 `/skills` 選擇 `tow-query`；在 Antigravity 中呼叫 `/tow-query`。

## 內容保留與選用的後續整理

僅變更中繼資料時，會使用獨立快照及 `tow verify-body`，檢查內文位元組是否完全一致。格式涵蓋 Markdown 語法、數學公式分隔符號、程式碼圍欄／依語言處理的格式，以及表格，但絕不變更其中的內容。模糊或無法驗證的修正只會回報。這些是技能指示加上範圍有限的位元組比對，並非通用的語意驗證器，也不是宿主強制執行的安全性掛鉤。

`tow-edit`、`tow-merge`、`tow-ingest` 和 `tow-review` 保留原有名稱，作為選用的後續整理工作流程。它們會重用你提供或既已確立的範本及規則；一般的清理要求或單獨一份範本，並不授權改寫已填寫的文字、產生樞紐筆記或拆分筆記。請見[內容保留](../docs/preservation.md)及[後續整理](../docs/post-curation.md)。

## 環境需求

- 支援外掛程式的 Claude Code、Codex 或 Google Antigravity
- Git，用於從 GitHub 安裝
- 使用選用的 `tag-ontology` 解析／本體功能時，需要 Node.js 22.18 以上版本，且 npm/npx 位於 `PATH` 中
- Obsidian CLI 為選用；原生搜尋需要啟用 CLI，且執行中的應用程式能存取目標 vault。沒有 CLI 時仍可使用檔案搜尋
- Python 3.10 以上版本（僅使用標準函式庫）

技能會讀取你限定範圍內的 vault 檔案，並且只套用你核准的變更。你的代理宿主會依照自身的模型及隱私設定處理已開啟筆記的內容。TOW 沒有託管後端；npm 會下載固定版本的 CLI，檔案存取則由宿主控制。

## 從 GitHub 安裝

直接從這個公開儲存庫安裝。是否登錄至官方目錄為選用。以下指令使用 `main`；安裝後請啟動新的宿主工作階段。有關驗證、vault 設定及更新，請見[安裝與疑難排解指南](../docs/installation.md)。

### Claude Code

```text
/plugin install tow --marketplace NamhyeonKo/tag-ontology-wiki
```

Claude Code 2.1.275 之前的版本：

```text
/plugin marketplace add NamhyeonKo/tag-ontology-wiki
/plugin install tow@tag-ontology-wiki
```

### Codex

在 shell 中執行：

```bash
codex plugin marketplace add NamhyeonKo/tag-ontology-wiki --ref main
codex plugin add tow@tag-ontology-wiki
```

### Antigravity

在 shell 中執行，然後啟動新的 Antigravity 工作階段：

```bash
agy plugin install https://github.com/NamhyeonKo/tag-ontology-wiki
```

## 更新

在終端機中執行對應宿主的指令，然後啟動新的工作階段。

**Claude Code：**

```bash
claude plugin update tow@tag-ontology-wiki
```

**Codex：**

```bash
codex plugin marketplace upgrade tag-ontology-wiki
codex plugin add tow@tag-ontology-wiki
```

**Antigravity：** 從相同來源重新安裝。

```bash
agy plugin install https://github.com/NamhyeonKo/tag-ontology-wiki
```

使用宿主的外掛程式清單／詳細資訊指令確認已安裝的版本。有關各宿主的行為及檢查方式，請見[更新與疑難排解](../docs/installation.md#update)。

## 首次使用

將 vault 作為宿主的工作區開啟。在新的工作階段中，使用上述對應宿主的呼叫方式選擇 `tow-query`，然後傳送：

```text
我的 vault 位於 /absolute/path/to/vault。請依類別或概念尋找與 RAG 相關的
專案筆記，排除已被取代的文件。請先閱讀符合的筆記再進行摘要，
並傳回它們的路徑及數量。不要修改檔案。
```

不必設定即可立即搜尋。如需選用的組織功能，請選擇 `tow-setup`；它會詢問你是否要採用 PARA，並保留現有的結構／結構描述。TOW 會讀取 vault 根目錄下的 `tow.json`；省略的設定會使用[設定指南](../docs/installation.md#configure-the-vault)中的預設值。安裝不會建立或遷移 vault。

## CLI 與設定檢查

輔助程式使用 `npx --yes tag-ontology@0.1.3`；npm 會在需要時取得該確切版本。手動執行輔助程式指令時，請使用已安裝的 `scripts/tow.py` 路徑。慣例中的名稱 `tow` 是該路徑的簡寫。

TOW 0.4.2 和 `tag-ontology` 0.1.3 都沒有 `doctor` 指令。請先執行：

```bash
python3 --version
node --version
npx --yes tag-ontology@0.1.3 --version
```

TOW 的 `lint` 僅應針對已採用的 TOW 中繼資料執行；字典檢查僅適用於已初始化的本體功能。缺少選用的中繼資料／字典不代表安裝失敗。接著依照[設定檢查](../docs/installation.md#check-the-setup)，驗證已安裝的外掛程式、設定、字典及筆記標籤。`lint` 涵蓋分類欄位及標籤數量；check 技能則另外逐篇檢視筆記格式／參照。單憑 lint 沒有問題的結果，無法涵蓋每一項技能檢查。

## 文件

- [安裝、vault 設定及疑難排解](../docs/installation.md)
- [vault 慣例及輔助程式指令](../docs/methodology.md)
- [內容保留](../docs/preservation.md)及[選用的後續整理](../docs/post-curation.md)
- [評估及驗證限制](../docs/evaluation.md)

詳細指南以英文維護，由所有語言版本的 README 共用。

## 參與貢獻

歡迎回報錯誤、提供範圍明確的修正、改善文件，以及更正翻譯。開發環境設定、檢查，以及技能參考資料與讀者用翻譯之間的區別，請閱讀 [CONTRIBUTING.md](../CONTRIBUTING.md)。請使用 [issue 表單](https://github.com/NamhyeonKo/tag-ontology-wiki/issues/new/choose)回報錯誤或提出功能建議。

## 支持

TOW 是免費的開放原始碼專案。如果它為你節省了時間，歡迎[請我喝杯咖啡](https://buymeacoffee.com/namhyunko)。

## 授權條款

[MIT](../LICENSE)
