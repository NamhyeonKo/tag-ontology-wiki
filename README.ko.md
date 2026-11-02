# TOW — Tag Ontology for Wiki

Obsidian 노트를 태그 중심으로 검색하고 관리하는 Claude Code·Codex·Google Antigravity 플러그인입니다.

[English](README.md)

> **버전:** 0.1.1.

## 개요

TOW는 Karpathy의 LLM Wiki를 변형해 노트를 태그 중심으로 정리하는 방법론입니다. 이 방법론을 따르는 vault는 세 층으로 구성됩니다.

- **PARA 폴더**: Projects, Areas, Resources, Archives.
- frontmatter의 **분류 필드**: `category`, `type`, `status`, `kind`.
- **개념 태그 온톨로지**: 별칭과 상하위 관계를 담은 태그 사전.

전체 규약은 [docs/methodology.md](docs/methodology.md)(영어)에 있습니다.

TOW는 로컬 코딩 에이전트에 네 가지 작업 절차를 설치합니다. vault와 대상 노트를 지정하면 에이전트가 파일을 읽고, 분류·개념 태그로 검색하고, 승인할 변경안을 제안합니다. 노트는 기존 Obsidian vault의 파일로 유지됩니다.

패키지는 스킬·공통 규약·Python helper인 [`scripts/tow.py`](scripts/tow.py)로 구성됩니다. helper는 분류 규칙을 검사하고, [`tag-ontology`](https://github.com/NamhyeonKo/obsidian-tag-ontology) npm CLI를 호출해 노트 파싱·태그 조회·사전 검증과 변경을 처리합니다. 모델과 파일 도구는 에이전트 호스트가 제공합니다.

```text
tag-ontology@0.1.2        사전 검증·조회·변경, 노트 파싱
      ▲  npx tag-ontology … --json
tow (이 플러그인)          vault 규약 검사, 스킬
      ▲  Claude Code / Codex / Antigravity
사용자의 Obsidian vault
```

## 스킬

| 스킬 | 이런 때 사용 | 변경 범위 |
| --- | --- | --- |
| `tow-query` | RAG 프로젝트 노트, 특정 category·개념에 해당하는 노트 찾기 | 읽기 전용. 요약할 노트는 먼저 엽니다. |
| `tow-check` | frontmatter·제목·표·수식·참조 검사 | 먼저 보고하고, 승인한 서식만 고칩니다. |
| `tow-tag-suggest` | 지정한 노트의 개념 태그 추천 | 사용자가 고른 추가·제거만 적용합니다. |
| `tow-tag-sync` | 새 태그 등록, 별칭 정리, 사전과 노트 태그 맞추기 | 먼저 제안하고, 승인한 사전·태그 변경만 적용합니다. |

세 호스트가 같은 스킬·규약·CLI를 공유합니다. Claude Code에서는 `/tow:tow-query`, Codex에서는 `$` 또는 `/skills`로 `tow-query` 선택, Antigravity에서는 `/tow-query`로 호출합니다.

## 요구 사항

- 플러그인을 지원하는 Claude Code, Codex 또는 Google Antigravity
- Git (GitHub에서 설치할 때 사용)
- Node.js 22.18 이상과 `PATH`에 등록된 npm/npx (`tag-ontology` CLI 실행용)
- Python 3.10 이상 (표준 라이브러리만 사용)

스킬은 지정한 vault 파일을 읽고 승인한 변경만 적용합니다. 열린 노트 내용은 에이전트 호스트의 모델·개인정보 설정에 따라 처리됩니다. TOW 자체 서버는 없으며, npm으로 고정 버전 CLI를 내려받고 파일 접근은 호스트가 제어합니다.

## GitHub에서 설치

공개 저장소에서 바로 설치합니다. 공식 디렉터리 등록은 선택 사항입니다. 아래 명령은 `main`을 사용하며, 설치 후 호스트에서 새 세션을 시작합니다. 설치 확인·vault 설정·업데이트는 [설치 및 문제 해결 가이드](docs/installation.ko.md)를 따르세요.

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

## 처음 사용하기

vault를 호스트의 작업 폴더로 열거나 해당 폴더에 접근 권한을 줍니다. 새 세션에서 위의 호스트별 방식으로 `tow-query`를 선택하고 다음처럼 요청합니다.

```text
내 vault는 /절대/경로/vault야. RAG 관련 프로젝트 노트를 category와 개념 태그로
찾아줘. 대체된 문서는 제외하고, 요약할 노트는 먼저 읽은 뒤 경로와 개수를 알려줘.
파일은 수정하지 마.
```

기존 vault에서는 폴더·사전 경로부터 확인합니다. TOW는 vault 루트의 `tow.json`을 읽고, 생략한 설정에는 [가이드의 기본값](docs/installation.ko.md#vault-설정)을 사용합니다. 설치 과정에서 vault를 생성하거나 이관하지는 않습니다.

## CLI와 설치 점검

helper가 사용하는 명령은 `npx --yes tag-ontology@0.1.2`입니다. 필요할 때 npm으로 해당 버전을 내려받습니다. 직접 실행할 때는 설치된 `scripts/tow.py` 경로를 사용합니다. 규약 문서의 `tow`는 이 경로를 줄여 쓴 이름입니다.

TOW 0.1.1과 `tag-ontology` 0.1.2 모두 `doctor` 명령은 없습니다. 먼저 다음을 확인합니다.

```bash
python3 --version
node --version
npx --yes tag-ontology@0.1.2 --version
```

이후 [설치 점검 절차](docs/installation.ko.md#설치-점검)로 플러그인·설정·사전·노트 태그를 확인합니다. `lint`는 분류 필드와 태그 수 등을 검사하고, check 스킬은 노트별 서식·참조 검토를 더합니다. lint 통과만으로 스킬의 모든 검사 항목을 확인한 것은 아닙니다.

## 개발

```bash
uv sync
uv run ruff check
uv run ruff format --check
uv run pyright
uv run pytest
```

스킬은 [`scripts/tow.py`](scripts/tow.py)를 부르고, 이 스크립트는 `npx --yes tag-ontology@0.1.2`로 노트를 읽습니다. 배포 시 내려받는 실행 파일을 재현할 수 있도록 정확한 버전을 고정합니다. 다른 빌드의 CLI를 쓰려면 `TOW_TAG_ONTOLOGY`에 그 명령을 넣습니다. 예: `TOW_TAG_ONTOLOGY="node /path/to/cli.js"`.

실제 CLI 연동 테스트는 로컬에서는 선택 사항입니다. `TOW_TAG_ONTOLOGY`에 CLI를 지정하면 단위 테스트와 함께 실행됩니다.

```bash
TOW_TAG_ONTOLOGY="npx --yes tag-ontology@0.1.2" uv run pytest
```

이 변수가 없으면 연동 테스트를 건너뜁니다. 테스트는 [합성 vault](tests/fixtures/vault)를 임시 디렉터리에 복사하며 사용자의 vault를 사용하지 않습니다. 스킬 평가 시나리오와 검증 한계는 [평가 문서](docs/evaluation.md)에 있습니다.

## 라이선스

[MIT](LICENSE)
