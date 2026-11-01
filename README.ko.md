# TOW — Tag Ontology for Wiki

Obsidian에서 태그 중심 LLM 위키를 운영하기 위한 Claude Code·Codex·Google Antigravity 플러그인입니다.

[English](README.md)

> **상태:** 개발 중이며 아직 릴리스 전입니다.

## 개요

TOW는 Karpathy의 LLM Wiki를 변형해 노트를 태그 중심으로 정리하는 방법론입니다. 이 방법론을 따르는 vault는 세 층으로 구성됩니다.

- **PARA 폴더**: Projects, Areas, Resources, Archives.
- frontmatter의 **분류 필드**: `category`, `type`, `status`, `kind`.
- **개념 태그 온톨로지**: 별칭과 상하위 관계를 담은 태그 사전.

전체 규약은 [docs/methodology.md](docs/methodology.md)(영어)에 있습니다.

이 플러그인은 에이전트가 이 규약을 따르게 하는 스킬과, vault 규약을 검사하는 Python 도구를 제공합니다.
사전 검증·조회·변경과 노트 파싱은 [`tag-ontology`](https://github.com/NamhyeonKo/obsidian-tag-ontology) CLI가 맡습니다. TOW는 CLI를 호출할 뿐 노트를 직접 파싱하지 않습니다.

```text
tag-ontology (npm CLI)    사전 검증·조회·변경, 노트 파싱
      ▲  npx tag-ontology … --json
tow (이 플러그인)          vault 규약 검사, 스킬
      ▲  Claude Code / Codex / Antigravity
사용자의 Obsidian vault
```

## 스킬

| 스킬 | 용도 |
| --- | --- |
| `tow-check` | 노트가 vault 규약과 태그 사전에 맞는지 검사 |
| `tow-tag-sync` | 노트에 쓰인 태그와 태그 사전을 맞춤 |
| `tow-tag-suggest` | 노트에 달 개념 태그를 추천하고, 사용자가 고른 것만 붙임 |
| `tow-query` | category나 개념 태그로 노트를 찾음 (읽기 전용) |

세 호스트가 같은 스킬·규약·CLI를 공유합니다. Claude Code에서는 `/tow:tow-query`, Codex에서는 `$` 또는 `/skills`로 `tow-query` 선택, Antigravity에서는 `/tow-query`로 호출합니다.

## 요구 사항

- 플러그인을 지원하는 Claude Code, Codex 또는 Google Antigravity
- Node.js 22.18 이상 (`tag-ontology` CLI 실행용)
- Python 3.10 이상 (표준 라이브러리만 사용)

## 설치

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

## 개발

```bash
uv sync
uv run ruff check
uv run ruff format --check
uv run pyright
uv run pytest
```

스킬은 [`scripts/tow.py`](scripts/tow.py)를 부르고, 이 스크립트는 `npx --yes tag-ontology@0.1`로 노트를 읽습니다. 다른 빌드의 CLI를 쓰려면 `TOW_TAG_ONTOLOGY`에 그 명령을 넣습니다. 예: `TOW_TAG_ONTOLOGY="node /path/to/cli.js"`.

실제 CLI 연동 테스트는 로컬에서는 선택 사항입니다. `TOW_TAG_ONTOLOGY`에 CLI를 지정하면 단위 테스트와 함께 실행됩니다.

```bash
TOW_TAG_ONTOLOGY="npx --yes tag-ontology@0.1" uv run pytest
```

이 변수가 없으면 연동 테스트를 건너뜁니다. 테스트는 [합성 vault](tests/fixtures/vault)를 임시 디렉터리에 복사하며 사용자의 vault를 사용하지 않습니다. 스킬 평가 시나리오와 검증 한계는 [평가 문서](docs/evaluation.md)에 있습니다.

## 라이선스

[MIT](LICENSE)
