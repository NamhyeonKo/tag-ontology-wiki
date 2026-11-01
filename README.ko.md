# TOW — Tag Ontology for Wiki

Obsidian에서 태그 중심 LLM 위키를 운영하기 위한 Claude Code 플러그인입니다.

[English](README.md)

> **상태:** 개발 중입니다. 스킬이 쓰는 `tag-ontology` CLI가 아직 배포되지 않았습니다.

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
      ▲  /plugin install
사용자의 Obsidian vault
```

## 스킬

| 스킬 | 용도 |
| --- | --- |
| `tow:tow-check` | 노트가 vault 규약과 태그 사전에 맞는지 검사 |
| `tow:tow-tag-sync` | 노트에 쓰인 태그와 태그 사전을 맞춤 |
| `tow:tow-tag-suggest` | 노트에 달 개념 태그를 추천하고, 사용자가 고른 것만 붙임 |
| `tow:tow-query` | category나 개념 태그로 노트를 찾음 (읽기 전용) |

## 요구 사항

- Claude Code
- Node.js (`tag-ontology` CLI 실행용)
- Python 3.10 이상 (표준 라이브러리만 사용)

## 설치

```text
/plugin install tow --marketplace NamhyeonKo/tag-ontology-wiki
```

Claude Code 2.1.275 미만:

```text
/plugin marketplace add NamhyeonKo/tag-ontology-wiki
/plugin install tow@tag-ontology-wiki
```

## 개발

```bash
uv sync
uv run ruff check
uv run ruff format --check
uv run pyright
uv run pytest
```

스킬은 [`scripts/tow.py`](scripts/tow.py)를 부르고, 이 스크립트는 `npx --yes tag-ontology`로 노트를 읽습니다. 다른 빌드의 CLI를 쓰려면 `TOW_TAG_ONTOLOGY`에 그 명령을 넣습니다. 예: `TOW_TAG_ONTOLOGY="node /path/to/cli.js"`.

## 라이선스

[MIT](LICENSE)
