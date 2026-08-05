# TIL

매일 배운 것을 월 단위 마크다운 파일에 기록한다. 사람이 쓰기 편한 형식을 유지하되,
헤더 라인만 정규식으로 잡을 수 있게 규칙을 고정해서 나중에 파싱할 수 있게 한다.

```
TIL/
├── 2026-08.md              # 월 단위 기록 파일
├── meta/
│   └── categories.md       # 카테고리 정의 + 변경 이력
├── tools/
│   └── parse_til.py        # 파서 겸 형식 검사기
└── .vscode/
    ├── til.code-snippets   # `til` + Tab 스니펫
    └── settings.json       # 스니펫이 뜨게 하는 설정
```

## 규칙 4가지

**1. 날짜는 `## YYYY-MM-DD`** — 하루에 하나. 그날 아무것도 안 배웠으면 날짜 자체를 안 쓴다.
빈 날짜 헤더를 남겨두지 않는다.

**2. 항목은 `### [카테고리] 제목`** — 대괄호 안은 `ML` `PYTHON` `SQL` `LEETCODE` `INFRA` `ETC`
6개만. 정의와 경계 판단 기준은 [meta/categories.md](meta/categories.md)에 있다.
카테고리를 자유롭게 늘리면 나중에 집계가 안 된다.

**3. 태그는 제목 바로 다음 줄에 `#태그` 한 줄** — 영문 소문자, 숫자, 하이픈만 쓴다 (`#time-series`).
한글과 영문을 섞으면 `#시계열`과 `#time-series`가 다른 태그로 집계된다. 태그는 카테고리보다
세분화된 자유 라벨이고 2~4개면 충분하다.

**4. 마커는 제목 끝에** — 이해가 덜 됐으면 `#review`, 나중에 해볼 것이면 `#todo`를 제목 끝에 붙인다.
태그 줄이 아니라 제목 줄에 붙여야 나중에 따로 뽑아낼 수 있다.

## 예시

````markdown
---
month: 2026-08
---

## 2026-08-05

### [ML] 케라스 학습 파이프라인
#keras #training

- 모델 생성 → compile → fit → evaluate → predict
- compile에서 손실함수, 옵티마이저, 학습률을 설정한다

### [PYTHON] pandas 조건부 집계
#pandas #groupby

```python
df.groupby('cat')['val'].agg(['mean', 'count'])
```

- agg에 리스트를 넘기면 컬럼이 MultiIndex로 생성됨

### [ML] 정밀도와 재현율 트레이드오프 #review
#metrics #classification

- threshold를 올리면 precision 상승, recall 하락
- 아직 PR curve 해석이 헷갈림

---

## 2026-08-06

### [LEETCODE] 121. Best Time to Buy and Sell Stock
#array #greedy

- 최소값을 갱신하며 한 번만 순회하면 O(n)

### [SQL] 윈도우 함수로 그룹별 순위
#window-function #rank

```sql
SELECT name, RANK() OVER (PARTITION BY dept ORDER BY salary DESC) FROM emp
```

- PARTITION BY가 GROUP BY와 달리 행을 줄이지 않는다

### [INFRA] git stash 정리
#git

- `git stash clear` 전체 삭제, `git stash drop stash@{n}` 개별 삭제
````

날짜 사이의 `---`는 있어도 되고 없어도 된다. 파서가 무시한다.

## 스니펫

VS Code에서 **TIL 폴더를 워크스페이스 루트로 열어야** 스니펫이 잡힌다
(상위 `KANT-AI` 폴더를 열면 안 된다). 마크다운 파일에서만 동작한다.

| 입력 | 결과 |
|---|---|
| `tilday` + Tab | 오늘 날짜 헤더 (`## 2026-08-05`, 날짜 자동) |
| `til` + Tab | 일반 항목 |
| `tilr` + Tab | 제목에 `#review`가 붙은 항목 |
| `tille` + Tab | 리트코드 항목 (번호·문제명 + 복잡도 + 코드 블록) |
| `tilcode` + Tab | 코드 블록만 (python/sql/bash/text 선택) |

`til` + Tab을 누르면 아래가 통째로 삽입되고, 커서는 `[ML]` 자리에 있다.

```
### [ML] 제목
#tag

- 배운 것
```

`제목` `tag` `배운 것`은 placeholder다. **선택된 상태로 들어오므로 지우지 말고 그냥 타이핑하면
덮어써진다.** Tab으로 다음 칸에 옮겨 다니면 된다.

1. **카테고리** — 드롭다운이 떠 있다. ↑↓로 고르고 Enter. 타이핑으로 필터링도 된다
   (`py` 치면 PYTHON). 드롭다운이 안 보이면 `⌃Space`.
2. **Tab** → `제목`이 선택된다. 그대로 제목을 친다.
3. **Tab** → `tag`가 선택된다. `#`는 이미 찍혀 있으니 이름만 친다.
   두 개 이상이면 `keras #training`처럼 이어서 친다.
4. **Tab** → `배운 것`이 선택된다. 본문을 친다. 여기서 스니펫이 끝나고 평소처럼 쓰면 된다.

`⇧Tab`으로 이전 칸에 돌아갈 수 있다. `Esc`를 누르면 칸 이동이 끊기니 다 채울 때까지 누르지 않는다.
placeholder를 그대로 두고 나오면 `- 배운 것` 같은 문구가 파일에 남으니, 안 쓸 칸은 지운다.
`tille`의 `O(?)`는 일부러 눈에 띄게 둔 것이라 안 채우면 바로 보인다.

동작하지 않으면:

- **Tab을 눌렀는데 그냥 들여쓰기만 된다** → `editor.tabCompletion`이 꺼진 것.
  [.vscode/settings.json](.vscode/settings.json)이 워크스페이스에 적용됐는지 확인한다.
- **입력 중 목록이 안 뜬다** → `⌃Space`로 직접 부른다. macOS에서 `⌃Space`가
  입력기 전환에 잡혀 있으면 시스템 설정 → 키보드 → 단축키에서 해제한다.
- **그래도 안 되면** → `⇧⌘P` → `Insert Snippet` → 목록에서 고른다. 이 방법은 항상 된다.

다른 폴더에서도 쓰고 싶으면 `⇧⌘P` → `Snippets: Configure Snippets` → `markdown`을 골라
전역 스니펫으로 옮기면 된다.

## 하루 입력 흐름

1. 그날의 월 파일을 연다. 새 달이면 `python3 tools/parse_til.py --new 2026-09`.
2. 날짜 헤더가 없으면 `tilday` + Tab.
3. 항목마다 `til` + Tab.
4. 가끔 `python3 tools/parse_til.py --lint`로 형식을 점검한다.

## 파싱

```bash
python3 tools/parse_til.py                      # 전체를 JSONL로 출력
python3 tools/parse_til.py --lint               # 형식 위반만 검사 (error 있으면 exit 1)
python3 tools/parse_til.py --tag review         # #review 붙은 항목만
python3 tools/parse_til.py --category LEETCODE  # 리트코드 항목만
python3 tools/parse_til.py --stats              # 카테고리/태그 집계
```

결과는 `{date, category, title, tags, markers, body, source}` 구조의 리스트라서 그대로
JSONL로 떨어뜨리거나, 임베딩을 태워서 검색 가능한 노트 데이터베이스로 만들 수 있다.
한 항목이 하나의 개념 단위라 청킹이 따로 필요 없다.

축약어 설명: `re` = regular expression (정규식), `m` = match 객체, `cur` = current entry (현재 처리 중인 항목).
