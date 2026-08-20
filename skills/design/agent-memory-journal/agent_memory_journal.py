#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

VERSION = '0.1.0'

LINE_RE = re.compile(r"^-\s+(\d{2}:\d{2})\s+(.*)$")
LONG_BULLET_RE = re.compile(r"^-\s+(.*)$")
DAILY_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")


class JournalPaths:
    def __init__(self, root: Path, memory_dir: str = 'memory', long_file: str = 'MEMORY.md'):
        self.root = root
        self.mem_dir = root / memory_dir
        self.long = root / long_file
        self.lock_file = root / '.agent_memory_journal.lock'

    def today_daily_path(self) -> Path:
        return self.mem_dir / f"{datetime.now().date()}.md"


def default_root() -> Path:
    env = os.environ.get('AGENT_MEMORY_ROOT')
    if env:
        return Path(env).expanduser().resolve()
    return Path.cwd()


def default_triggers():
    return [
        r'\bremember\b',
        r'\bdecision\b',
        r'\bdecided\b',
        r'\bfrom now on\b',
        r'\balways\b',
        r'\bpriority\b',
    ]


def load_config(paths: "JournalPaths", config_file: str | None = None) -> dict:
    if config_file:
        candidate = Path(config_file).expanduser()
        if not candidate.is_absolute():
            candidate = paths.root / candidate
    else:
        candidate = paths.root / 'agent-memory-journal.json'
    if not candidate.exists():
        return {'triggers': default_triggers(), 'config_path': None}
    data = json.loads(candidate.read_text(encoding='utf-8'))
    triggers = data.get('triggers') or default_triggers()
    return {'triggers': triggers, 'config_path': str(candidate)}


@contextmanager
def global_lock(paths: JournalPaths):
    paths.root.mkdir(parents=True, exist_ok=True)
    with paths.lock_file.open('a+', encoding='utf-8') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def normalize_note(note: str) -> str:
    text = note.strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\W_]+", "", text, flags=re.UNICODE)
    return text


def tokenize(text: str) -> list[str]:
    return [w.lower() for w in re.findall(r"[A-Za-zÅÄÖåäö0-9-]{3,}", text)]


def is_recent_duplicate(paths: JournalPaths, note: str, window_minutes: int) -> bool:
    if window_minutes <= 0:
        return False

    target = normalize_note(note)
    now = datetime.now()
    files_with_date: list[tuple[Path, datetime.date]] = [(paths.today_daily_path(), now.date())]
    if window_minutes > now.hour * 60 + now.minute:
        yday = now.date() - timedelta(days=1)
        files_with_date.append((paths.mem_dir / f"{yday}.md", yday))

    for daily, file_date in files_with_date:
        if not daily.exists():
            continue
        try:
            lines = daily.read_text(encoding='utf-8', errors='ignore').splitlines()
        except Exception:
            continue
        for ln in reversed(lines):
            m = LINE_RE.match(ln.strip())
            if not m:
                continue
            hhmm, existing_note = m.group(1), m.group(2)
            try:
                ts = datetime.combine(file_date, datetime.strptime(hhmm, '%H:%M').time())
            except ValueError:
                continue
            age_min = (now - ts).total_seconds() / 60
            if age_min < 0:
                continue
            if age_min > window_minutes:
                break
            if normalize_note(existing_note) == target:
                return True
    return False


def has_long_duplicate(paths: JournalPaths, note: str) -> bool:
    if not paths.long.exists():
        return False
    target = normalize_note(note)
    try:
        lines = paths.long.read_text(encoding='utf-8', errors='ignore').splitlines()
    except Exception:
        return False
    for ln in lines:
        m = LONG_BULLET_RE.match(ln.strip())
        if not m:
            continue
        if normalize_note(m.group(1)) == target:
            return True
    return False


def append_daily(paths: JournalPaths, note: str, dedupe_minutes: int = 0) -> bool:
    daily = paths.today_daily_path()
    paths.mem_dir.mkdir(parents=True, exist_ok=True)
    if is_recent_duplicate(paths, note, dedupe_minutes):
        return False
    ts = datetime.now().strftime('%H:%M')
    with daily.open('a', encoding='utf-8') as f:
        f.write(f"- {ts} {note.strip()}\n")
    return True


def append_long(paths: JournalPaths, note: str, dedupe: bool = True) -> bool:
    if dedupe and has_long_duplicate(paths, note):
        return False
    if not paths.long.exists():
        paths.long.write_text('# MEMORY.md\n\n', encoding='utf-8')
    with paths.long.open('a', encoding='utf-8') as f:
        f.write(f"\n- {note.strip()}\n")
    return True


def init_memory_root(paths: JournalPaths, with_config: bool = False) -> dict:
    paths.root.mkdir(parents=True, exist_ok=True)
    paths.mem_dir.mkdir(parents=True, exist_ok=True)
    created = []
    if not paths.long.exists():
        paths.long.write_text('# MEMORY.md\n\n', encoding='utf-8')
        created.append(str(paths.long))
    if with_config:
        cfg = paths.root / 'agent-memory-journal.json'
        if not cfg.exists():
            cfg.write_text(json.dumps({'triggers': default_triggers()}, indent=2) + '\n', encoding='utf-8')
            created.append(str(cfg))
    return {'created': created, 'root': str(paths.root)}


def extract_candidates(text: str, triggers=None):
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out = []
    for ln in lines:
        low = ln.lower()
        if any(re.search(t, low) for t in (triggers or default_triggers())):
            out.append(ln)
    return out


def iter_daily_files(paths: JournalPaths, days: int, after_date=None, before_date=None):
    if not paths.mem_dir.exists():
        return []
    rolling_cutoff = datetime.now().date() - timedelta(days=max(0, days - 1))
    min_date = max(rolling_cutoff, after_date) if after_date else rolling_cutoff
    max_date = before_date
    candidates = []
    for p in paths.mem_dir.glob('*.md'):
        m = DAILY_FILE_RE.match(p.name)
        if not m:
            continue
        try:
            d = datetime.strptime(m.group(1), '%Y-%m-%d').date()
        except ValueError:
            continue
        if d < min_date:
            continue
        if max_date and d > max_date:
            continue
        candidates.append((d, p))
    return [p for _d, p in sorted(candidates, key=lambda x: x[0], reverse=True)]


def parse_iso_date(value: str):
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid date '{value}', expected YYYY-MM-DD") from exc


def collect_recent(paths: JournalPaths, days: int, limit: int, grep: str | None):
    files = iter_daily_files(paths, days)
    if not files:
        return []
    pattern = re.compile(grep, re.IGNORECASE) if grep else None
    out = []
    for p in files:
        date = p.stem
        try:
            lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
        except Exception:
            continue
        for ln in reversed(lines):
            m = LINE_RE.match(ln.strip())
            if not m:
                continue
            hhmm, note = m.group(1), m.group(2)
            if pattern and not pattern.search(note):
                continue
            out.append({'date': date, 'time': hhmm, 'note': note})
            if len(out) >= limit:
                return out
    return out


def print_recent(paths: JournalPaths, days: int, limit: int, grep: str | None, as_json: bool = False):
    items = collect_recent(paths, days, limit, grep)
    if as_json:
        print(json.dumps(items, ensure_ascii=False))
        return
    files = iter_daily_files(paths, days)
    if not files:
        print('NO_MEMORY_FILES')
        return
    if not items:
        print('NO_MATCHES')
        return
    for item in items:
        print(f"{item['date']} {item['time']} {item['note']}")


def search_notes(paths: JournalPaths, query: str, days: int, limit: int, regex: bool = False, source: str = 'all', after_date=None, before_date=None):
    if regex:
        pattern = re.compile(query, re.IGNORECASE)
        matcher = lambda text: bool(pattern.search(text))
    else:
        needle = query.strip().lower()
        matcher = lambda text: needle in text.lower()
    out = []
    if source in ('all', 'long') and paths.long.exists():
        try:
            for idx, line in enumerate(paths.long.read_text(encoding='utf-8', errors='ignore').splitlines(), start=1):
                if matcher(line):
                    out.append({'source': 'long', 'path': str(paths.long), 'line': idx, 'text': line})
                    if len(out) >= limit:
                        return out
        except Exception:
            pass
    if source in ('all', 'daily'):
        for p in iter_daily_files(paths, days, after_date, before_date):
            try:
                lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
            except Exception:
                continue
            for idx, line in enumerate(lines, start=1):
                if matcher(line):
                    out.append({'source': 'daily', 'path': str(p), 'line': idx, 'text': line})
                    if len(out) >= limit:
                        return out
    return out


def print_search(paths: JournalPaths, **kwargs):
    as_json = kwargs.pop('as_json', False)
    items = search_notes(paths, **kwargs)
    if as_json:
        print(json.dumps(items, ensure_ascii=False))
        return
    if not items:
        print('NO_MATCHES')
        return
    for item in items:
        print(f"{item['source']} {item['path']}:{item['line']} {item['text']}")


def _note_words(paths: JournalPaths, days: int):
    files = iter_daily_files(paths, days)
    words = []
    notes = []
    stop = {
        'the','and','for','with','that','this','from','have','was','were','are','but','not','into','out','new','added','gained','now','also','recent','notes',
        'että','joka','tämä','tuo','ovat','oli','kun','tai','jos','nyt','sekä','vielä','kanssa','uusi','lisätty'
    }
    for p in files:
        try:
            lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
        except Exception:
            continue
        for ln in lines:
            m = LINE_RE.match(ln.strip())
            if not m:
                continue
            note = m.group(2)
            notes.append(note)
            words.extend(w.lower() for w in re.findall(r"[A-Za-zÅÄÖåäö0-9-]{3,}", note) if w.lower() not in stop)
    return notes, words


def memory_stats(paths: JournalPaths, days: int = 7, top: int = 10):
    files = iter_daily_files(paths, days)
    note_count = 0
    hourly = Counter()
    daily_counts = Counter()
    notes, words = _note_words(paths, days)
    for p in files:
        try:
            lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
        except Exception:
            continue
        for ln in lines:
            m = LINE_RE.match(ln.strip())
            if not m:
                continue
            hhmm = m.group(1)
            hour = hhmm.split(':')[0]
            note_count += 1
            hourly[hour] += 1
            daily_counts[p.stem] += 1
    return {
        'days_scanned': days,
        'files_found': len(files),
        'days_with_notes': len(daily_counts),
        'note_count': note_count,
        'busiest_hours': [{'hour': h, 'count': c} for h, c in hourly.most_common(3)],
        'top_words': [{'word': w, 'count': c} for w, c in Counter(words).most_common(top)],
    }


def memory_topics(paths: JournalPaths, days: int = 14, top: int = 8, samples: int = 2, min_count: int = 2):
    notes, words = _note_words(paths, days)
    counts = Counter(words)
    word_samples = {}
    for note in notes:
        tokens = set(tokenize(note))
        for word, count in counts.items():
            if count < min_count:
                continue
            if word in tokens:
                word_samples.setdefault(word, [])
                if len(word_samples[word]) < samples and note not in word_samples[word]:
                    word_samples[word].append(note)
    topics = []
    for word, count in counts.most_common():
        if count < min_count:
            continue
        topics.append({'word': word, 'count': count, 'samples': word_samples.get(word, [])})
        if len(topics) >= max(1, top):
            break
    return {'days_scanned': days, 'note_count': len(notes), 'topics': topics}


def print_stats(paths: JournalPaths, days: int = 7, top: int = 10, as_json: bool = False):
    stats = memory_stats(paths, days=max(1, days), top=max(1, top))
    if as_json:
        print(json.dumps(stats, ensure_ascii=False))
        return
    print(f"days_scanned={stats['days_scanned']} files_found={stats['files_found']} days_with_notes={stats['days_with_notes']} note_count={stats['note_count']}")
    if stats['busiest_hours']:
        print('busiest_hours: ' + ', '.join(f"{h['hour']}:00({h['count']})" for h in stats['busiest_hours']))
    if stats['top_words']:
        print('top_words: ' + ', '.join(f"{w['word']}({w['count']})" for w in stats['top_words']))


def print_topics(paths: JournalPaths, days: int = 14, top: int = 8, samples: int = 2, min_count: int = 2, as_json: bool = False):
    summary = memory_topics(paths, days=max(1, days), top=max(1, top), samples=max(1, samples), min_count=max(1, min_count))
    if as_json:
        print(json.dumps(summary, ensure_ascii=False))
        return
    print(f"days_scanned={summary['days_scanned']} note_count={summary['note_count']} topics={len(summary['topics'])}")
    for topic in summary['topics']:
        print(f"- {topic['word']}({topic['count']}): {' | '.join(topic['samples'])}")


def memory_cadence(paths: JournalPaths, days: int = 14, top_hours: int = 3):
    files = iter_daily_files(paths, days)
    per_day = []
    hourly = Counter()
    for p in files:
        count = 0
        try:
            lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
        except Exception:
            continue
        for ln in lines:
            m = LINE_RE.match(ln.strip())
            if not m:
                continue
            count += 1
            hourly[m.group(1).split(':')[0]] += 1
        per_day.append({'date': p.stem, 'count': count})
    return {'days_scanned': days, 'per_day': per_day, 'busiest_hours': [{'hour': h, 'count': c} for h, c in hourly.most_common(top_hours)]}


def print_cadence(paths: JournalPaths, days: int = 14, top_hours: int = 3, as_json: bool = False):
    summary = memory_cadence(paths, days=max(1, days), top_hours=max(1, top_hours))
    if as_json:
        print(json.dumps(summary, ensure_ascii=False))
        return
    print('per_day: ' + ', '.join(f"{d['date']}({d['count']})" for d in summary['per_day']))
    print('busiest_hours: ' + ', '.join(f"{h['hour']}:00({h['count']})" for h in summary['busiest_hours']))


def memory_digest(paths: JournalPaths, days: int = 7, recent_limit: int = 5, top: int = 5):
    stats = memory_stats(paths, days=max(1, days), top=max(1, top))
    cadence = memory_cadence(paths, days=max(1, days), top_hours=max(1, min(top, 3)))
    topics = memory_topics(paths, days=max(1, days), top=max(1, top), samples=1, min_count=2)
    recent = collect_recent(paths, days=max(1, days), limit=max(1, recent_limit), grep=None)
    return {'days_scanned': days, 'stats': stats, 'cadence': cadence, 'topics': topics, 'recent': recent}


def print_digest(paths: JournalPaths, days: int = 7, recent_limit: int = 5, top: int = 5, as_json: bool = False):
    summary = memory_digest(paths, days=max(1, days), recent_limit=max(1, recent_limit), top=max(1, top))
    if as_json:
        print(json.dumps(summary, ensure_ascii=False))
        return
    stats = summary['stats']; cadence = summary['cadence']; topics = summary['topics']; recent = summary['recent']
    print(f"days_scanned={summary['days_scanned']} files_found={stats['files_found']} days_with_notes={stats['days_with_notes']} note_count={stats['note_count']}")
    if cadence['busiest_hours']:
        print('busiest_hours: ' + ', '.join(f"{h['hour']}:00({h['count']})" for h in cadence['busiest_hours']))
    if topics['topics']:
        print('topics: ' + ', '.join(f"{item['word']}({item['count']})" for item in topics['topics']))
    else:
        print('topics: none')
    if recent:
        print('recent_notes:')
        for item in recent:
            print(f"- {item['date']} {item['time']} {item['note']}")
    else:
        print('recent_notes: none')


def memory_candidates(paths: JournalPaths, days: int = 7, limit: int = 10, min_score: int = 2, triggers=None):
    topic_words = {item['word'] for item in memory_topics(paths, days=max(1, days), top=20, samples=1, min_count=2)['topics']}
    out = []
    for p in iter_daily_files(paths, days):
        try:
            lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
        except Exception:
            continue
        for ln in lines:
            m = LINE_RE.match(ln.strip())
            if not m:
                continue
            note = m.group(2)
            low = note.lower()
            tokens = set(tokenize(note))
            score = 0
            triggered = [t for t in (triggers or default_triggers()) if re.search(t, low)]
            if triggered:
                score += len(triggered)
            if any(word in tokens for word in topic_words):
                score += 1
            if len(note) > 80:
                score += 1
            if score >= min_score:
                out.append({'date': p.stem, 'note': note, 'score': score})
    out.sort(key=lambda x: (-x['score'], x['date']), reverse=False)
    return {'days_scanned': days, 'candidates': out[: max(1, limit)]}


def print_candidates(paths: JournalPaths, days: int = 7, limit: int = 10, min_score: int = 2, as_json: bool = False, triggers=None):
    summary = memory_candidates(paths, days=max(1, days), limit=max(1, limit), min_score=max(1, min_score), triggers=triggers)
    if as_json:
        print(json.dumps(summary, ensure_ascii=False))
        return
    if not summary['candidates']:
        print('NO_CANDIDATES')
        return
    for item in summary['candidates']:
        print(f"{item['score']} {item['date']} {item['note']}")


def build_parser():
    ap = argparse.ArgumentParser(
        description='Durable memory journal for agents and operators',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  agent-memory-journal --root /workspace add --note \"Remember to rotate PAT\"\n"
            "  agent-memory-journal --root /workspace recent --days 2\n"
            "  agent-memory-journal --root /workspace digest --days 7"
        ),
    )
    ap.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
    ap.add_argument('--root', type=Path, default=default_root(), help='Memory root directory (default: $AGENT_MEMORY_ROOT or current directory)')
    ap.add_argument('--memory-dir', default='memory', help='Daily memory directory relative to root (default: memory)')
    ap.add_argument('--long-file', default='MEMORY.md', help='Long-term memory filename relative to root (default: MEMORY.md)')
    ap.add_argument('--config-file', help='Optional JSON config path relative to root or absolute')
    sub = ap.add_subparsers(dest='cmd', required=True)

    a = sub.add_parser('add', help='Append a note to daily memory')
    a.add_argument('--note', required=True)
    a.add_argument('--long', action='store_true')
    a.add_argument('--dedupe-minutes', type=int, default=0)
    a.add_argument('--no-long-dedupe', action='store_true')

    i = sub.add_parser('init', help='Bootstrap a new memory root')
    i.add_argument('--with-config', action='store_true', help='Create starter agent-memory-journal.json too')

    ex = sub.add_parser('extract', help='Extract likely memory-worthy lines from stdin or file')
    ex.add_argument('--file', type=Path)

    r = sub.add_parser('recent', help='Show newest daily memory notes across recent days')
    r.add_argument('--days', type=int, default=2)
    r.add_argument('--limit', type=int, default=20)
    r.add_argument('--grep')
    r.add_argument('--json', action='store_true')

    s = sub.add_parser('search', help='Search long and daily notes for text matches')
    s.add_argument('--query', required=True)
    s.add_argument('--days', type=int, default=30)
    s.add_argument('--limit', type=int, default=20)
    s.add_argument('--regex', action='store_true')
    s.add_argument('--source', choices=['all', 'long', 'daily'], default='all')
    s.add_argument('--after', type=parse_iso_date)
    s.add_argument('--before', type=parse_iso_date)
    s.add_argument('--json', action='store_true')

    st = sub.add_parser('stats', help='Summarize recent daily memory activity')
    st.add_argument('--days', type=int, default=7)
    st.add_argument('--top', type=int, default=10)
    st.add_argument('--json', action='store_true')

    tp = sub.add_parser('topics', help='Surface recurring note topics with sample references')
    tp.add_argument('--days', type=int, default=14)
    tp.add_argument('--top', type=int, default=8)
    tp.add_argument('--samples', type=int, default=2)
    tp.add_argument('--min-count', type=int, default=2)
    tp.add_argument('--json', action='store_true')

    cd = sub.add_parser('cadence', help='Show daily note volume and busiest hours')
    cd.add_argument('--days', type=int, default=14)
    cd.add_argument('--top-hours', type=int, default=3)
    cd.add_argument('--json', action='store_true')

    dg = sub.add_parser('digest', help='Print a compact operational digest')
    dg.add_argument('--days', type=int, default=7)
    dg.add_argument('--recent-limit', type=int, default=5)
    dg.add_argument('--top', type=int, default=5)
    dg.add_argument('--json', action='store_true')

    cc = sub.add_parser('candidates', help='Surface likely long-term memory candidates')
    cc.add_argument('--days', type=int, default=7)
    cc.add_argument('--limit', type=int, default=10)
    cc.add_argument('--min-score', type=int, default=2)
    cc.add_argument('--json', action='store_true')
    return ap


def main():
    ap = build_parser()
    args = ap.parse_args()
    paths = JournalPaths(args.root.expanduser().resolve(), args.memory_dir, args.long_file)
    config = load_config(paths, args.config_file)
    triggers = config['triggers']
    with global_lock(paths):
        if args.cmd == 'init':
            result = init_memory_root(paths, with_config=args.with_config)
            print(json.dumps(result, ensure_ascii=False))
        elif args.cmd == 'add':
            added_daily = append_daily(paths, args.note, dedupe_minutes=args.dedupe_minutes)
            print('OK: note stored' if added_daily else 'SKIP_DUPLICATE: recent identical note exists')
            if args.long:
                added_long = append_long(paths, args.note, dedupe=not args.no_long_dedupe)
                print('LONG_OK' if added_long else 'LONG_SKIP_DUPLICATE')
        elif args.cmd == 'extract':
            text = args.file.read_text(encoding='utf-8') if args.file else __import__('sys').stdin.read()
            c = extract_candidates(text, triggers=triggers)
            print(json.dumps(c, ensure_ascii=False, indent=2))
        elif args.cmd == 'recent':
            print_recent(paths, days=max(1, args.days), limit=max(1, args.limit), grep=args.grep, as_json=args.json)
        elif args.cmd == 'search':
            print_search(paths, query=args.query, days=max(1, args.days), limit=max(1, args.limit), regex=args.regex, source=args.source, after_date=args.after, before_date=args.before, as_json=args.json)
        elif args.cmd == 'stats':
            print_stats(paths, days=max(1, args.days), top=max(1, args.top), as_json=args.json)
        elif args.cmd == 'topics':
            print_topics(paths, days=max(1, args.days), top=max(1, args.top), samples=max(1, args.samples), min_count=max(1, args.min_count), as_json=args.json)
        elif args.cmd == 'cadence':
            print_cadence(paths, days=max(1, args.days), top_hours=max(1, args.top_hours), as_json=args.json)
        elif args.cmd == 'digest':
            print_digest(paths, days=max(1, args.days), recent_limit=max(1, args.recent_limit), top=max(1, args.top), as_json=args.json)
        elif args.cmd == 'candidates':
            print_candidates(paths, days=max(1, args.days), limit=max(1, args.limit), min_score=max(1, args.min_score), as_json=args.json, triggers=triggers)


if __name__ == '__main__':
    main()
