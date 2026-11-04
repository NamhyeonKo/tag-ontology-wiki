# TOW — Tag Ontology for Wiki

**Obsidian vault 내부 문서 관리용 에이전트 스킬 플러그인**입니다. vault를 작업 폴더로 열어 노트 검색·frontmatter 관리·내용을 보존하는 형식 교정을 수행하며, Claude Code·Codex·Google Antigravity에서 실행됩니다.

[English](../README.md) · [한국어](README.ko.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Français](README.fr.md)

> **버전:** 0.4.2.

## 개요

일반 관리에서는 문장·수식과 코드의 내용·표 값을 보존하고, 선택한 frontmatter와 형식만 변경합니다. 별도 사후 관리는 사용자의 템플릿·규칙과 명시한 작업 범위를 따릅니다. TOW는 frontmatter가 없는 노트와 기존 폴더 구조에서도 사용할 수 있습니다. 선택 사항인 태그 중심 LLM Wiki 규약은 다음 세 층으로 구성됩니다.

- **PARA 폴더**: Projects, Areas, Resources, Archives.
- frontmatter의 **분류 필드**: `category`, `type`, `status`, `kind`.
- **개념 태그 온톨로지**: 별칭과 상하위 관계를 담은 태그 사전.

초기 설정에서 PARA 사용 여부를 선택하며, 원하지 않으면 기존 구조를 유지합니다. 일반 검색·본문 작업에는 사전이나 메타데이터 정리가 필요하지 않습니다. 검색은 Obsidian CLI 우선 → 범위를 지정한 파일 검색 보완 → 내용 확인 순서이며, 기존 속성이 있으면 정확도를 높이는 데 활용합니다. 전체 규약은 [docs/methodology.md](../docs/methodology.md)(영어)에 있습니다.

TOW는 로컬 코딩 에이전트에 열한 가지 작업 절차를 설치합니다. vault와 대상 노트를 지정하면 에이전트가 파일을 읽고, 분류·개념 태그로 검색하고, 승인할 변경안을 제안합니다. 노트는 기존 Obsidian vault의 파일로 유지됩니다.

패키지는 스킬·공통 규약·Python helper인 [`scripts/tow.py`](../scripts/tow.py)로 구성됩니다. helper는 분류 규칙을 검사하고, [`tag-ontology`](https://github.com/NamhyeonKo/obsidian-tag-ontology) npm CLI를 호출해 노트 파싱·태그 조회·사전 검증과 변경을 처리합니다. 모델과 파일 도구는 에이전트 호스트가 제공합니다.

TOW는 Tag Ontology의 CLI를 활용해 태그를 조회하고 사전을 검증·관리합니다. [Obsidian용 Tag Ontology 플러그인](https://github.com/NamhyeonKo/obsidian-tag-ontology)([커뮤니티 플러그인 페이지](https://community.obsidian.md/plugins/tag-ontology))을 함께 설치하면, 관리한 태그의 계층과 관계를 그래프로 시각적으로 확인할 수 있습니다.

```text
tag-ontology@0.1.3        사전 검증·조회·변경, 노트 파싱
      ▲  npx tag-ontology … --json
tow (이 플러그인)          vault 규약 검사, 스킬
      ▲  Claude Code / Codex / Antigravity
사용자의 Obsidian vault
```

## 스킬

| 스킬 | 이런 때 사용 | 변경 범위 |
| --- | --- | --- |
| `tow-setup` | PARA 또는 기존 구조 선택, 필요한 사전만 선택적으로 설정 | 최상위 폴더만 확인. 승인 뒤 폴더·사전·`tow.json`만 만들고 노트는 옮기지 않습니다. |
| `tow-query` | 자연어 조건·사용자 속성·태그·본문으로 문서 찾기 | 읽기 전용. CLI 우선, 파일 검색 보완, 확인된 결과와 추정 후보 구분. |
| `tow-check` | frontmatter·Markdown·수식·코드·표·참조 검사 | 먼저 보고하고, 문장·내부 내용·값을 보존하는 승인한 구문만 고칩니다. |
| `tow-tag-suggest` | 지정한 노트의 개념 태그 추천 | 사용자가 고른 추가·제거만 적용합니다. |
| `tow-tag-sync` | 새 태그 등록, 별칭 정리, 사전과 노트 태그 맞추기 | 먼저 제안하고, 승인한 사전·태그 변경만 적용합니다. |
| `tow-classify` | 카테고리 등록·재분류·구 분류 태그 이관 | 등록·이관을 승인받고, 기존 노트 소급 적용은 별도로 결정합니다. |
| `tow-link` | 제목·별칭이 언급된 곳에 위키링크 연결 | 승인한 첫 언급만 연결하고 표시 문구를 보존합니다. |
| `tow-edit` | 사용자 템플릿·규칙에 따른 명시적 본문 사후 관리 | 선택한 새 내용·빈 절·변환만 처리하고, 필요한 규칙이 없으면 묻습니다. |
| `tow-merge` | 선택한 목적지·규칙에 따른 명시적 통합 | 원문 이동이 기본이며, 병합 건별 선택·사실 폐기는 따로 확인합니다. |
| `tow-review` | 사용자 규칙에 따른 점검·사후 관리 제안 | 구체적 후속 작업을 선택하기 전에는 읽기 전용입니다. |
| `tow-ingest` | 선택한 규칙에 따른 파일 정리·출처 사후 관리 | 원문 그대로 정리가 기본이며, 메타데이터·파생·재작성을 자동 추가하지 않습니다. |

세 호스트가 같은 스킬·규약·CLI를 공유합니다. Claude Code에서는 `/tow:tow-query`, Codex에서는 `$` 또는 `/skills`로 `tow-query` 선택, Antigravity에서는 `/tow-query`로 호출합니다.

## 본문 보존과 선택적 사후 관리

메타데이터만 수정할 때는 독립적인 원본·후보 사본과 `tow verify-body`로 본문 바이트가 같은지 확인합니다. 형식 교정에는 Markdown 문법, 수식 구분자, 코드 펜스·언어별 형식, 표가 포함되지만 내부 내용과 값은 바꾸지 않습니다. 모호하거나 검증할 수 없는 수정은 보고만 합니다. 이 비교 도구는 의미 동등성을 모두 증명하거나 호스트 차원에서 모든 위반을 차단하는 기능은 아닙니다.

`tow-edit`·`tow-merge`·`tow-ingest`·`tow-review`는 이름을 유지하고 선택적 사후 관리로 사용합니다. 사용자가 제공하거나 기존에 정한 템플릿·규칙을 활용하며, 일반적인 정리 요청이나 템플릿만으로 채워진 본문 재작성·허브 생성·노트 분리를 허용하지 않습니다. [보존 계약](../docs/preservation.md)과 [사후 관리 계약](../docs/post-curation.md)을 참고하세요.

## 요구 사항

- 플러그인을 지원하는 Claude Code, Codex 또는 Google Antigravity
- Git (GitHub에서 설치할 때 사용)
- `tag-ontology` 파싱·온톨로지 기능을 사용할 때 Node.js 22.18 이상과 `PATH`에 등록된 npm/npx
- Obsidian CLI는 선택 사항입니다. 활성화와 실행 중인 앱의 대상 vault 접근이 필요하며, 사용할 수 없으면 파일 검색으로 보완합니다.
- Python 3.10 이상 (표준 라이브러리만 사용)

스킬은 지정한 vault 파일을 읽고 승인한 변경만 적용합니다. 열린 노트 내용은 에이전트 호스트의 모델·개인정보 설정에 따라 처리됩니다. TOW 자체 서버는 없으며, npm으로 고정 버전 CLI를 내려받고 파일 접근은 호스트가 제어합니다.

## GitHub에서 설치

공개 저장소에서 바로 설치합니다. 공식 디렉터리 등록은 선택 사항입니다. 아래 명령은 `main`을 사용하며, 설치 후 호스트에서 새 세션을 시작합니다. 설치 확인·vault 설정·업데이트는 [설치 및 문제 해결 가이드](../docs/installation.md)(영어)를 따르세요.

### Claude Code

```text
/plugin install tow --marketplace NamhyeonKo/tag-ontology-wiki
```

Claude Code 2.1.275 미만:

```text
/plugin marketplace add NamhyeonKo/tag-ontology-wiki
/plugin install tow@tag-ontology-wiki
```

### Codex

셸에서 실행합니다.

```bash
codex plugin marketplace add NamhyeonKo/tag-ontology-wiki --ref main
codex plugin add tow@tag-ontology-wiki
```

### Antigravity

셸에서 실행한 뒤 새 Antigravity 세션을 시작합니다.

```bash
agy plugin install https://github.com/NamhyeonKo/tag-ontology-wiki
```

## 업데이트

터미널에서 호스트에 맞는 명령을 실행한 뒤 새 세션을 시작합니다.

**Claude Code:**

```bash
claude plugin update tow@tag-ontology-wiki
```

**Codex:**

```bash
codex plugin marketplace upgrade tag-ontology-wiki
codex plugin add tow@tag-ontology-wiki
```

**Antigravity:** 같은 소스에서 다시 설치합니다.

```bash
agy plugin install https://github.com/NamhyeonKo/tag-ontology-wiki
```

호스트의 플러그인 목록·상세 정보 명령으로 설치된 버전을 확인합니다. 호스트별 동작과 확인 절차는 [업데이트 및 문제 해결](../docs/installation.md#update)(영어)을 참고하세요.

## 처음 사용하기

vault를 호스트의 작업 폴더로 엽니다. 새 세션에서 위의 호스트별 방식으로 `tow-query`를 선택하고 다음처럼 요청합니다.

```text
내 vault는 /절대/경로/vault야. RAG 관련 프로젝트 노트를 category와 개념 태그로
찾아줘. 대체된 문서는 제외하고, 요약할 노트는 먼저 읽은 뒤 경로와 개수를 알려줘.
파일은 수정하지 마.
```

설정 없이 바로 검색할 수 있습니다. 정리 기능을 설정하려면 `tow-setup`을 선택하세요. PARA 사용 여부를 먼저 묻고 기존 구조·속성을 보존합니다. TOW는 vault 루트의 `tow.json`을 읽고, 생략한 설정에는 [가이드의 기본값](../docs/installation.md#configure-the-vault)을 사용합니다. 설치 과정에서 vault를 생성하거나 이관하지는 않습니다.

## CLI와 설치 점검

helper가 사용하는 명령은 `npx --yes tag-ontology@0.1.3`입니다. 필요할 때 npm으로 해당 버전을 내려받습니다. 직접 실행할 때는 설치된 `scripts/tow.py` 경로를 사용합니다. 규약 문서의 `tow`는 이 경로를 줄여 쓴 이름입니다.

TOW 0.4.2와 `tag-ontology` 0.1.3 모두 `doctor` 명령은 없습니다. 먼저 다음을 확인합니다.

```bash
python3 --version
node --version
npx --yes tag-ontology@0.1.3 --version
```

TOW `lint`는 해당 메타데이터 규약을 채택한 노트에, 사전 검사는 온톨로지를 초기화한 경우에 적용합니다. 선택하지 않은 메타데이터·사전이 없다는 것은 설치 실패가 아닙니다. 이후 [설치 점검 절차](../docs/installation.md#check-the-setup)로 플러그인·설정·사전·노트 태그를 확인합니다. `lint`는 분류 필드와 태그 수 등을 검사하고, check 스킬은 노트별 서식·참조 검토를 더합니다. lint 통과만으로 스킬의 모든 검사 항목을 확인한 것은 아닙니다.

## 문서

- [설치·vault 설정·문제 해결](../docs/installation.md)
- [vault 규약과 helper 명령](../docs/methodology.md)
- [내용 보존](../docs/preservation.md)과 [선택적 사후 관리](../docs/post-curation.md)
- [평가와 검증 한계](../docs/evaluation.md)

상세 안내는 영어로 관리하며 모든 언어의 README가 같은 문서를 공유합니다.

## 기여하기

버그 제보, 범위를 좁힌 수정, 문서 개선, 번역 교정을 환영합니다. 개발 환경·검사 방법·스킬 참조 문서와 독자용 번역의 구분은 [CONTRIBUTING.md](../CONTRIBUTING.md)를 참고하세요. 버그 제보와 기능 제안에는 [Issue 양식](https://github.com/NamhyeonKo/tag-ontology-wiki/issues/new/choose)을 사용합니다.

## 후원

TOW는 무료 오픈 소스입니다. 시간을 아껴 줬다면 [커피 한 잔](https://buymeacoffee.com/namhyunko)을 선물해 주셔도 좋습니다.

## 라이선스

[MIT](../LICENSE)
