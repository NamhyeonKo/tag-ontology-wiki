# GitHub에서 TOW 설치하고 사용하기

[English](installation.md) · [개요](../README.ko.md)

TOW는 Obsidian vault 내부 문서 관리를 위한 열한 개 스킬을 로컬 에이전트 호스트에 추가합니다. vault를 작업 폴더로 열고, 함께 설치된 Python helper와 선택적인 npm `tag-ontology` CLI를 사용합니다. 공개 GitHub 저장소에서 설치하며, 공식 디렉터리 신청은 필요하지 않습니다.

## 호스트에 설치

호스트에서 Git과 Python 3.10+를 실행할 수 있어야 합니다. Node.js 22.18+와 npm/npx는 선택적인 `tag-ontology` 파싱·온톨로지 기능에 필요하며, 파일 검색·본문 작업에는 필수가 아닙니다. 첫 CLI 실행 시 npm에서 `tag-ontology@0.1.2`를 내려받을 수 있습니다. 모델·계정·파일 권한·개인정보 설정은 호스트의 것을 사용하며, TOW의 별도 서비스나 API 키는 없습니다.

**Claude Code — Claude Code 세션 안에서 실행:**

```text
/plugin install tow --marketplace NamhyeonKo/tag-ontology-wiki
```

Claude Code 2.1.275 미만에서는 다음 두 명령을 사용합니다.

```text
/plugin marketplace add NamhyeonKo/tag-ontology-wiki
/plugin install tow@tag-ontology-wiki
```

**Codex — 터미널에서 실행:**

```bash
codex plugin marketplace add NamhyeonKo/tag-ontology-wiki --ref main
codex plugin add tow@tag-ontology-wiki --json
```

**Antigravity — 터미널에서 실행:**

```bash
agy plugin install https://github.com/NamhyeonKo/tag-ontology-wiki
```

설치 후 호스트에서 새 세션을 시작하고 Obsidian vault를 작업 폴더로 엽니다. 검색·선택한 편집·파일 정리 목적지는 해당 vault 안으로 한정합니다.

## 플러그인 로드 확인

해당 호스트의 명령을 터미널에서 실행합니다.

| 호스트 | 설치 확인 | 새 세션에서 스킬 선택 |
| --- | --- | --- |
| Claude Code | `claude plugin details tow@tag-ontology-wiki` | `/tow:tow-query` |
| Codex | `codex plugin list --json` | `$` 또는 `/skills`에서 `tow-query` 선택 |
| Antigravity | `agy plugin list --json` | `/tow-query` |

`tow`, 버전 `0.4.0`, 표시되는 경우 활성화 상태를 확인합니다. 새 세션의 스킬 선택 목록에서 `tow-query`·`tow-check`·`tow-tag-suggest`·`tow-tag-sync`와 새 워크플로 `tow-classify`·`tow-link`·`tow-edit`·`tow-merge`·`tow-review`·`tow-ingest`·`tow-setup`까지 열한 개를 확인합니다. Claude의 `plugin details`는 구성 요소를 보여주며, `claude plugin list --json`에는 설치 경로와 활성화 상태도 나옵니다. Codex 설치 결과에는 `installedPath`가 나오지만 plugin list 자체는 스킬 목록이 아닙니다. Antigravity 목록에는 `path`와 발견한 스킬이 나옵니다.

## vault 설정

TOW는 `<vault>/tow.json`을 읽습니다. 파일이 없으면 다음 기본값을 사용합니다.

```json
{
  "projects": "01_Projects",
  "areas": "02_Areas",
  "resources": "03_Resources",
  "archives": "04_Archives",
  "projectArchive": "archive",
  "tagDictionary": "Tag-Dictionary.json",
  "categoryDictionary": "Category-Dictionary.md",
  "inbox": "00_Inbox",
  "attachments": "99_Etc/attachments",
  "dailyNotes": "02_Areas/daily-notes",
  "misc": "99_Etc",
  "scope": "para"
}
```

실제 vault와 다른 값만 지정하면 됩니다. 예를 들어 폴더가 `Projects`, `Areas`, `Resources`, `Archives`이고 프로젝트 이력 폴더가 `superseded`, 사전이 `meta/`에 있다면 다음처럼 설정합니다.

```json
{
  "projects": "Projects",
  "areas": "Areas",
  "resources": "Resources",
  "archives": "Archives",
  "projectArchive": "superseded",
  "tagDictionary": "meta/Tag-Dictionary.json",
  "categoryDictionary": "meta/Category-Dictionary.md",
  "inbox": "Capture",
  "attachments": "Support/media",
  "dailyNotes": "Areas/journal",
  "misc": "Support"
}
```

네 PARA 폴더명은 vault 바로 아래의 폴더를 뜻합니다. `projectArchive`는 `Projects/Search/superseded/`처럼 프로젝트 안에 두는 이력 폴더 이름이며, 검색 범위 안에서는 어느 깊이에 있든 같은 이름의 폴더를 인식합니다. 사전 경로는 vault 루트 기준입니다. 태그 사전은 개념 항목을 담은 JSON 객체, category 사전은 등록된 분류 값의 Markdown 인덱스입니다. 형식은 [공통 규약](methodology.md)에 있습니다.

`inbox`·`misc`도 vault 바로 아래 폴더명입니다. `attachments`·`dailyNotes`는 vault 안의 상대 경로이며 절대 경로·`..`·vault 루트는 허용하지 않습니다. 다른 설정을 바꿔도 이 경로들이 자동으로 따라 바뀌지는 않습니다. 이 경로는 캡처 범위·첨부 이동·링크 제외에 사용되며 기본 PARA 검색 범위를 넓히지 않습니다.

`scope`는 경로 없이 실행하는 검색·점검이 읽는 범위입니다. `para`(기본값)는 네 PARA 폴더만, `vault`는 inbox·지원·이력 폴더까지 모든 노트 폴더를 읽고, 명시적으로 선택하지 않은 category 사전만 제외합니다. 기존 구조를 유지하려면 `vault`를 쓰세요. 이 설정은 TOW 메타데이터 규약 채택을 뜻하지 않으며, 비공개·미선택 파일은 검사 전에 제외해야 합니다.

### 새 vault나 기존 vault에서 시작하기

설치 과정에서 vault 파일은 만들어지지 않습니다. frontmatter나 사전 없이도 검색·본문 작업을 시작할 수 있습니다. 설정이 필요하면 `tow-setup`을 선택하세요. 에이전트는 이름만 확인한 뒤 **PARA 사용 여부를 먼저 묻습니다.** 빈 vault도 마찬가지입니다.

| 사용자 선택 | 설정 |
| --- | --- |
| PARA 사용 | 기존 폴더를 재사용·매핑하거나 없는 폴더를 제안. inbox·사전은 별도로 선택 |
| 기존 구조 사용 또는 PARA 미사용 | 폴더·노트를 보존하고 helper 검색용 `{"scope": "vault"}`만 제안 |

승인 전에는 아무것도 쓰지 않습니다. PARA·TOW 메타데이터·태그 온톨로지는 독립적인 선택입니다. 초기 설정은 노트를 옮기거나 속성을 추가하지 않으며, 원하는 목적지로 정리하는 일은 `tow-ingest`로 요청합니다.

helper의 기존 PARA 기본값은 유지합니다. 일반 vault(`scope: vault`)에서는 기본 `init`이 아무것도 생성하지 않으며, `--dictionaries`를 지정해야 빈 사전 두 개를 제안합니다. inbox나 PARA 폴더는 만들지 않습니다.

```bash
"$TOW" --root "$VAULT" init                       # 미리 보기, 파일 변경 없음
"$TOW" --root "$VAULT" init --dictionaries        # 사전을 선택적으로 제안
"$TOW" --root "$VAULT" init --dictionaries --apply
```

`--apply`는 미리 보기에 나온 항목을 모두 승인한 경우에만 사용합니다. 일부만 필요하면 스킬이 승인한 파일만 따로 생성합니다.

## 설치 점검

TOW 0.4.0과 `tag-ontology` 0.1.2에는 `doctor` 명령이 없습니다. 다음 중 적용되는 항목만 vault 수정 없이 점검합니다. 사용자 스키마에는 TOW lint를 적용하지 않고, 온톨로지를 선택하지 않았으면 사전 검사도 생략합니다. 미적용·실행 불가를 통과나 설치 실패로 표시하지 않습니다.

**1. 런타임 버전 — 터미널 (Node/npm은 온톨로지·파싱용):**

```bash
python3 --version
node --version
npx --yes tag-ontology@0.1.2 --version
```

마지막 명령은 `0.1.2`를 출력해야 합니다. npm CLI를 실행할 수 있는지 확인하는 단계이며, vault 검사까지 하지는 않습니다.

**2. 설치된 helper — 터미널:**

`--help`·`config`는 모든 vault에서 확인할 수 있습니다. 아래 lint·사전 명령은 해당 TOW 규약·사전을 채택한 경우에만 실행하며, 사용자 속성을 강제로 검사하지 않습니다.

위의 호스트별 설치 정보로 `scripts/tow.py`를 찾고, 아래 두 절대 경로를 바꿉니다. `TOW`에는 스크립트 경로 하나만 담고 실행할 때 따옴표로 감쌉니다. bash와 zsh 모두에서 공백이 있는 경로도 처리합니다.

```bash
TOW="/설치된/tow의/절대/경로/scripts/tow.py"
VAULT="/vault의/절대/경로"
"$TOW" --help
"$TOW" --root "$VAULT" config
"$TOW" --root "$VAULT" lint
"$TOW" --root "$VAULT" ontology check --json
"$TOW" --root "$VAULT" ontology usage --json
```

| 점검 | 의미 |
| --- | --- |
| `--help` | Python helper가 실행되고 `config`·`init`·`lint`·`verify-body`·`find`·`ontology` 명령이 표시됨 |
| `config` | 합쳐진 설정을 출력함. 실제 폴더·사전과 비교해야 하며, 이 명령 자체가 파일 존재 여부를 검증하지는 않음 |
| `lint` | CLI로 노트를 읽고 분류 값·필드 범위·중복 태그·태그 수 등을 검사함. 깨끗하면 `OK` 출력 |
| `ontology check --json` | 태그 사전 검사. 깨끗하면 `ok: true`, 빈 `issues` 출력 |
| `ontology usage --json` | 제외 경로를 뺀 설정 범위를 읽고 frontmatter·본문 태그를 사전과 비교함. 결과와 실제 읽기 범위를 확인 |

이 명령들은 vault를 수정하지 않습니다. npm은 패키지 캐시를 쓸 수 있습니다. 규약·태그 문제는 vault 내용에 대한 결과이며, 그 자체가 설치 실패를 뜻하지는 않습니다. helper의 규약 lint는 frontmatter 없는 노트를 건너뛰므로 `tow-check`가 이를 직접 확인합니다. 서식·링크·태그 계층의 의미도 스킬의 검토가 필요합니다.

위의 경로 없는 검사는 설정한 검색 범위(기본은 PARA 폴더)를 읽습니다. `scope: para`인데 PARA 폴더가 없으면 결과 없이 끝나는 대신 경고를 냅니다. CLI는 `.gitignore`를 자동 적용하지 않습니다. `lint`·`ontology scan`에는 승인한 파일 경로를 지정합니다. `usage <경로>`도 미사용 태그 계산을 위해 제외 경로를 뺀 설정 범위 전체를 읽고, `show`도 `--notes` 없이 같은 범위를 읽습니다. 실제 전체 읽기 범위를 허용했거나 미선택 경로를 사전에 안전하게 제외한 경우에만 사용합니다. 그렇지 않으면 범위를 지정한 scan과 필요한 사전 항목을 확인하고 집계 검사는 미실행으로 표시합니다. `find`에는 경로·제외 옵션이 없으므로 전체 범위를 허용하지 않았다면 `ontology scan`을 사용합니다. [범위 규칙](methodology.md#scope-before-reading-note-contents)을 참고하세요.

호스트에 같은 점검을 요청할 수도 있습니다.

```text
내 vault는 /vault의/절대/경로야. 설치된 TOW helper로 런타임 버전,
적용된 설정, 사전 무결성, 노트 태그 사용 상태를 확인해줘.
설정된 폴더와 사전 파일이 실제로 있는지도 보고, 파일 수정 없이 결과만 알려줘.
```

## 내용 보존과 사후 관리

일반 관리에서는 선택한 frontmatter와 형식만 변경합니다. Markdown·수식·코드·표의 **내용과 값**은 유지하고, 모호한 수정은 보고만 합니다. `tow-check`는 문장 재작성·수식 단순화·알고리즘 수정·빈 셀 채우기를 하지 않습니다. 표의 기존 정렬 등 표현 방식은 사용자의 규칙·템플릿을 따릅니다.

메타데이터만 수정할 때는 먼저 원본의 비공개·ignore 경계를 보존하는 사본 위치를 정합니다. 숨김 폴더만으로는 충분하지 않으며, Git vault에서는 복사 전에 후보 경로가 `git check-ignore`를 통과해야 합니다. 보호된 위치가 없으면 생성·ignore 변경을 먼저 제안합니다. 승인 후 독립 사본을 만들고, `BATCH`에 선택한 보호된 vault 상대 경로를 넣어 확인합니다.

```bash
"$TOW" --root "$VAULT" verify-body "$BATCH/before.md" "$BATCH/candidate.md"
```

종료 코드 0은 본문 바이트 동일, 1은 본문 변경, 2는 비교 불가·잘못된 입력입니다. 두 파일은 vault 안의 독립 사본이어야 하며 자기 비교·하드 링크는 거부합니다. Node·사전·`tow.json` 없이 실행되지만 YAML 변경의 적절성이나 형식 수정의 의미 동등성을 검증하는 명령은 아닙니다. 작업별 검증은 [보존 계약](preservation.md)에 있습니다.

`tow-edit`·`tow-merge`·`tow-ingest`·`tow-review`는 이름을 유지하며 [선택적 사후 관리](post-curation.md)에 사용합니다. 작업·대상·사용자 템플릿·규칙을 지정하세요. 원문 그대로 파일을 옮길 때는 목적지 선택만으로 충분합니다. 본문 생성·채워진 절 재작성·병합·분리·허브 생성은 정리·lint·review의 부수 효과가 아니라 별도로 명시할 작업입니다.

## 스킬 활용

스킬을 명시적으로 선택하고 vault 루트와 작업할 파일·폴더를 적습니다. Claude는 스킬 앞에 `/tow:`, Antigravity는 `/`를 붙이며, Codex에서는 `$` 또는 `/skills`로 선택합니다.

| 스킬 | 선택 후 요청 예시 |
| --- | --- |
| `tow-setup` | “/vault/절대/경로를 설정해줘. PARA 사용 여부를 먼저 묻고, 기존 구조를 보존하며 승인한 항목만 만들어줘.” |
| `tow-query` | “RAG 관련 프로젝트 노트를 category와 개념 태그로 찾아줘. 대체 문서는 빼고, 찾은 노트를 읽은 뒤 경로와 개수를 알려줘.” |
| `tow-check` | “이 두 노트의 frontmatter·제목·표·수식·깨진 참조를 검사해줘. 먼저 보고만 하고 수정하지 마.” |
| `tow-tag-suggest` | “이 노트의 개념 태그를 추천해줘. 추가·제거 후보와 이유를 나누고 내 선택을 기다려줘.” |
| `tow-tag-sync` | “이 폴더의 태그를 사전과 대조해줘. 새 항목·별칭·중복 상위 태그 정리안을 제안하고 승인을 기다려줘.” |
| `tow-classify` | “이 노트들의 카테고리를 제안해줘. 먼저 등록하고, 기존 노트 소급 적용은 따로 물어봐.” |
| `tow-link` | “이 폴더의 기존 언급에 링크를 걸어줘. 대상·제외·모호·대상 없음 항목을 먼저 보여줘.” |
| `tow-edit` | “Templates/Concept.md와 지정한 출처를 사용해 이 노트의 빈 예시 절만 채워줘. 이미 채운 내용과 메타데이터는 유지해줘.” |
| `tow-merge` | “두 노트의 병합 전략과 보존할 사실·손실을 보여주고, 건별 선택을 기다려줘.” |
| `tow-review` | “이 도메인의 소유권·중복·허브 누락·고립을 점검하고 수정안을 먼저 보여줘.” |
| `tow-ingest` | “설정한 inbox 최상위 캡처의 메타데이터·목적지·첨부·링크를 포함한 intake 계획을 보여줘.” |

명확한 `tow-edit` 요청도 사용자 규칙·템플릿·출처와 보존 범위가 정해진 경우에만 선택한 본문 수정을 허용합니다. 필요한 규칙이 없으면 질문하고, 내장 템플릿을 임의로 대신 적용하지 않습니다. review는 구체적인 후속 작업을 선택하기 전에는 읽기 전용입니다. 다른 변경 작업은 먼저 제안합니다. intake/review의 배치 승인을 받아도 병합 건별 선택·사실 폐기 확인·카테고리 소급 결정은 별도로 유지합니다. 무시되거나 비공개인 캡처는 경로를 명시해야 하며, 추적·공개 범위로 이동하는 변화는 계획에 표시합니다. 공유 첨부는 별도 승인 없이 옮기지 않습니다.

예를 들어 Claude Code에서 `/tow:tow-tag-suggest`를 선택하고 노트를 지정합니다. 제안을 받은 뒤 “`semantic-chunking`만 추가하고 `information-retrieval`을 제거해줘. 나머지 태그와 본문은 유지해줘”처럼 변경을 고릅니다. `tow-tag-sync`는 사전 변경안을 plan으로 확인한 뒤 승인한 변경을 적용합니다. 승인 대기는 스킬 지침이며, 실제 도구 접근과 권한 창은 호스트가 제어합니다.

직접 검색하려면 다음처럼 실행할 수 있습니다.

```bash
"$TOW" --root "$VAULT" find ai/rag --type project
"$TOW" --root "$VAULT" find --type project --status in-progress
"$TOW" --root "$VAULT" ontology show rag --notes --json
```

첫 명령은 `category` 필드를, 세 번째는 개념 태그와 그 하위 개념을 검색합니다. 예시 값은 실제 사전에 맞게 바꿉니다. 노트 조회는 설정된 검색 범위를 사용합니다. PARA 범위에서 `find`와 ontology `show`는 `--all` 없이 프로젝트 이력을 제외하고, 일반 vault 범위에서는 이력 이름의 폴더도 포함합니다. 합집합·교집합 검색은 [query 스킬](../skills/tow-query/SKILL.md)에 설명되어 있습니다.

## 업데이트와 문제 해결

Claude Code는 `claude plugin update tow@tag-ontology-wiki`를 실행합니다. Codex는 `codex plugin marketplace upgrade tag-ontology-wiki`로 마켓을 새로 받은 뒤 `codex plugin add tow@tag-ontology-wiki`를 실행합니다. 현재 Antigravity CLI에는 별도 update 명령이 없으므로 GitHub 설치 명령으로 패키지를 다시 설치합니다. 결과 버전을 확인하고 새 세션을 시작하세요. Claude는 플러그인 버전으로 캐시하므로 변경된 패키지를 일반 업데이트로 받으려면 버전이 올라야 합니다.

| 증상 | 확인할 것 |
| --- | --- |
| 호스트에 plugin 명령이 없음 | 호스트 도움말·버전과 플러그인 지원 여부 |
| 스킬이 보이지 않음 | TOW 활성화 상태 확인 → 새 세션 시작 → 스킬 명시 선택 |
| 사전을 못 찾거나 검색 결과가 예상과 다름 | 대상 vault와 검색 범위 확인. 선택하지 않은 사전은 검색 필수가 아니며, 사전 생성은 `tow init --dictionaries`로 미리 보기 |
| `npx`를 못 찾거나 npm 오류가 남 | 호스트의 Node/npm `PATH`, 레지스트리 접근, 캐시 권한과 실제 npm 오류 |
| 호스트 사용량 한도·권한 거부 | 해당 호스트에서 해결하고, 승인은 의도한 vault·명령 범위로 유지 |

예시는 macOS의 Claude Code 2.1.310, Codex CLI 0.159.2, Antigravity CLI 1.4.12에서 확인했습니다. 합성 vault 평가 결과와 한계는 [평가 문서](evaluation.md)에 있습니다. 설치 명령 근거: [Claude Code](https://code.claude.com/docs/en/plugins/publish), [Codex](https://developers.openai.com/plugins/build/plugins), [Antigravity](https://antigravity.google/docs/plugins).

## 자연어 검색과 사용자 속성

`tow-query`는 [Obsidian CLI 검색](https://obsidian.md/help/cli)으로 속성·본문 태그·텍스트를 먼저 찾고, 사용할 수 없거나 결과가 부족하면 허용한 파일 범위에서 직접 검색한 뒤 조건을 검증합니다. frontmatter·사전·사전 설정은 필요하지 않습니다. 속성 조건은 파싱한 값으로 확인하며, 없는 상태 값은 미확인으로 남기고 추정 후보는 정확한 일치와 구분합니다. helper의 `find`는 frontmatter 태그만 다룹니다. ontology scan은 frontmatter·본문 태그를 나누어 출력하고, show·usage는 둘을 합쳐 집계합니다. `show --exact`는 반환하는 노트 경로만 좁히며 읽기 범위와 rollup 집계는 좁히지 않습니다. 위의 범위 규칙을 먼저 적용하세요.
