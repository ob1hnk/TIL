#!/usr/bin/env python3
"""TIL 마크다운 파서 겸 형식 검사기.

월 파일(`YYYY-MM.md`)을 읽어 항목 단위로 쪼갠다. 한 항목은
`{date, category, title, tags, markers, body, source}` 구조이고,
하나의 개념 단위라 그대로 JSONL로 떨어뜨리거나 임베딩에 태울 수 있다.

축약어: re = regular expression (정규식), m = match 객체, cur = current entry (현재 항목).

    python tools/parse_til.py                  # 전체를 JSONL로 출력
    python tools/parse_til.py --lint           # 형식 위반만 검사
    python tools/parse_til.py --tag review     # #review 붙은 항목만
    python tools/parse_til.py --category DSA   # DSA 항목만
    python tools/parse_til.py --stats          # 카테고리/태그 집계
    python tools/parse_til.py --new 2026-09    # 새 월 파일 생성
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# meta/categories.md의 닫힌 목록과 같아야 한다.
CATEGORIES = ["ML", "STAT", "PYTHON", "SQL", "DSA", "INFRA", "ETC"]
MARKERS = {"review", "todo"}

MONTH_FILE = re.compile(r"^\d{4}-\d{2}\.md$")
DATE = re.compile(r"^## (\d{4}-\d{2}-\d{2})\s*$")
# 제목은 lazy 매칭이라 뒤에 붙은 #마커를 삼키지 않는다.
# 마커 자리는 일부러 느슨하게 잡아서, 잘못된 마커도 조용히 제목에 섞이지 않고 lint에 걸리게 한다.
ENTRY = re.compile(r"^### \[([A-Za-z]+)\] (.+?)((?:\s+#[^\s#]+)*)\s*$")
TAG_LINE = re.compile(r"^#[^\s#]+(?:\s+#[^\s#]+)*\s*$")
TAG = re.compile(r"#([^\s#]+)")
VALID_TAG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
FENCE = re.compile(r"^\s*(?:```|~~~)")


def parse_file(path: Path) -> tuple[list[dict], list[tuple]]:
    """월 파일 하나를 항목 리스트와 형식 위반 리스트로 만든다."""
    entries: list[dict] = []
    problems: list[tuple] = []
    file_month = path.stem

    def report(lineno: int, level: str, msg: str) -> None:
        problems.append((path.name, lineno, level, msg))

    date = None
    cur = None
    in_front = False
    in_fence = False
    expect_tags = False
    date_lines: dict[str, int] = {}
    date_counts: Counter = Counter()
    prev_date = None

    for no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.rstrip()

        # --- front matter ---------------------------------------------------
        if no == 1 and line == "---":
            in_front = True
            continue
        if in_front:
            if line == "---":
                in_front = False
            elif line.startswith("month:"):
                declared = line.split(":", 1)[1].strip()
                if declared != file_month:
                    report(no, "error", f"front matter month({declared})가 파일명({file_month})과 다름")
            continue

        # --- 코드 블록: 안쪽의 `#`는 태그도 헤더도 아니다 ----------------------
        if FENCE.match(line):
            in_fence = not in_fence
            expect_tags = False
            if cur is not None:
                cur["body"].append(line)
            continue
        if in_fence:
            if cur is not None:
                cur["body"].append(line)
            continue

        # --- 날짜 헤더 -------------------------------------------------------
        if m := DATE.match(line):
            date = m.group(1)
            cur = None
            expect_tags = False
            if date in date_lines:
                report(no, "error", f"{date} 날짜 헤더 중복 (첫 등장 {date_lines[date]}행)")
            else:
                date_lines[date] = no
            if not date.startswith(file_month + "-"):
                report(no, "error", f"{date}는 {file_month}.md에 있으면 안 됨")
            if prev_date and date < prev_date:
                report(no, "warn", f"{date}가 앞선 {prev_date}보다 과거 (시간순 정렬 아님)")
            prev_date = date
            continue

        # --- 항목 헤더 -------------------------------------------------------
        if m := ENTRY.match(line):
            category, title, trailing = m.group(1), m.group(2).strip(), m.group(3)
            markers = TAG.findall(trailing)
            if date is None:
                report(no, "error", "날짜 헤더 없이 항목이 시작됨")
            if category not in CATEGORIES:
                report(no, "error", f"[{category}]는 정의되지 않은 카테고리 (meta/categories.md 참고)")
            for mk in markers:
                if mk not in MARKERS:
                    report(no, "warn", f"제목 끝의 #{mk}는 정의된 마커가 아님 (태그라면 다음 줄에)")
            cur = {
                "date": date,
                "category": category,
                "title": title,
                "tags": [],
                "markers": markers,
                "body": [],
                "source": f"{path.name}:{no}",
            }
            entries.append(cur)
            date_counts[date] += 1
            expect_tags = True
            continue

        # --- 제목 바로 다음 줄 = 태그 줄 ---------------------------------------
        if expect_tags:
            expect_tags = False
            if not line.strip():
                report(no - 1, "warn", f"'{cur['title']}'에 태그 줄이 없음")
                continue
            if TAG_LINE.match(line):
                tags = TAG.findall(line)
                for t in tags:
                    if not VALID_TAG.match(t):
                        report(no, "error", f"#{t}: 태그는 영문 소문자·숫자·하이픈만 (한글 금지)")
                cur["tags"] = tags
                continue
            report(no, "warn", f"'{cur['title']}' 다음 줄이 태그 줄이 아님")
            # 태그 줄이 아니면 본문으로 흘려보낸다.

        # --- 본문 -------------------------------------------------------------
        if cur is not None:
            if line.strip() == "---":  # 날짜 사이 구분선
                cur = None
                continue
            cur["body"].append(line)

    for d, lineno in date_lines.items():
        if date_counts[d] == 0:
            report(lineno, "error", f"{d} 날짜 헤더가 비어 있음 (배운 게 없으면 날짜를 쓰지 않는다)")

    for e in entries:  # 본문 앞뒤의 빈 줄 정리
        while e["body"] and not e["body"][0].strip():
            e["body"].pop(0)
        while e["body"] and not e["body"][-1].strip():
            e["body"].pop()

    return entries, problems


def month_files(paths: list[Path]) -> list[Path]:
    if paths:
        return paths
    return sorted(p for p in ROOT.glob("*.md") if MONTH_FILE.match(p.name))


def create_month(month: str) -> int:
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        print(f"YYYY-MM 형식이 아님: {month}", file=sys.stderr)
        return 1
    path = ROOT / f"{month}.md"
    if path.exists():
        print(f"이미 있음: {path}", file=sys.stderr)
        return 1
    path.write_text(f"---\nmonth: {month}\n---\n\n", encoding="utf-8")
    print(path)
    return 0


def print_stats(entries: list[dict]) -> None:
    dates = {e["date"] for e in entries}
    print(f"항목 {len(entries)}개 / 기록한 날 {len(dates)}일")

    print("\n[카테고리]")
    counts = Counter(e["category"] for e in entries)
    for code in CATEGORIES:
        if counts[code]:
            print(f"  {code:<9} {counts[code]}")

    print("\n[태그 상위 15]")
    for tag, n in Counter(t for e in entries for t in e["tags"]).most_common(15):
        print(f"  #{tag:<20} {n}")

    markers = Counter(m for e in entries for m in e["markers"])
    if markers:
        print("\n[마커]")
        for mk, n in markers.most_common():
            print(f"  #{mk:<8} {n}")


def main() -> int:
    ap = argparse.ArgumentParser(description="TIL 마크다운 파서 겸 형식 검사기")
    ap.add_argument("paths", nargs="*", type=Path, help="월 파일 (생략하면 저장소 전체)")
    ap.add_argument("--lint", action="store_true", help="형식 위반만 출력 (error가 있으면 exit 1)")
    ap.add_argument("--stats", action="store_true", help="카테고리·태그 집계")
    ap.add_argument("--tag", help="해당 태그 또는 마커가 붙은 항목만")
    ap.add_argument("--category", help="해당 카테고리 항목만")
    ap.add_argument("--new", metavar="YYYY-MM", help="새 월 파일 생성 후 종료")
    args = ap.parse_args()

    if args.new:
        return create_month(args.new)

    entries: list[dict] = []
    problems: list[tuple] = []
    files = month_files(args.paths)
    if not files:
        print("월 파일(YYYY-MM.md)이 없음", file=sys.stderr)
        return 1
    for path in files:
        e, p = parse_file(path)
        entries += e
        problems += p

    if args.lint:
        for name, lineno, level, msg in sorted(problems, key=lambda x: (x[0], x[1])):
            print(f"{name}:{lineno}: [{level}] {msg}")
        errors = sum(1 for p in problems if p[2] == "error")
        warns = len(problems) - errors
        print(f"\n항목 {len(entries)}개 검사 — error {errors}, warn {warns}")
        return 1 if errors else 0

    if problems:
        print(f"형식 위반 {len(problems)}건 — --lint로 확인", file=sys.stderr)

    if args.category:
        entries = [e for e in entries if e["category"] == args.category.upper()]
    if args.tag:
        want = args.tag.lstrip("#")
        entries = [e for e in entries if want in e["tags"] or want in e["markers"]]

    if args.stats:
        print_stats(entries)
        return 0

    for e in entries:
        print(json.dumps(e, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
