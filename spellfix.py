#!/usr/bin/env python3
import os, re, sys, requests
from typing import Dict, List, Tuple

LT_URL = os.environ.get("SPELLFIX_LT_URL", "http://127.0.0.1:8081/v2/check")
LANG = os.environ.get("SPELLFIX_LANG", "en-US")
TIMEOUT = float(os.environ.get("SPELLFIX_TIMEOUT", "2.8"))
MAX_CHUNK_CHARS = int(os.environ.get("SPELLFIX_MAX_CHUNK", "1200"))

# --- Brand / token normalization (never split / never recase weirdly) ---
BRANDS = ["SpellFix"]  # add more if you want
BRAND_RE = re.compile(r'\b(?:' + "|".join(re.escape(b) for b in BRANDS) + r')\b', re.IGNORECASE)

# --- Protection patterns ---
URL_RE = re.compile(r'\b(?:https?://|ftp://|www\.)[^\s<>()"]+', re.IGNORECASE)
EMAIL_RE = re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', re.IGNORECASE)

CAMEL_RE = re.compile(r'\b[a-z]+[A-Z][A-Za-z0-9]*\b')
SNAKE_RE = re.compile(r'\b[A-Za-z0-9]+(?:_[A-Za-z0-9]+)+\b')
KEBAB_RE = re.compile(r'\b[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+\b')

# Protect dot-identifiers ONLY if they look code-like (underscore/digits/Uppercase segments),
# so prose like "spaces.after" can be fixed.
DOT_IDENT_RE = re.compile(
    r'\b(?=[A-Za-z_])'
    r'(?:[A-Za-z_][A-Za-z0-9_]*\.)+'
    r'[A-Za-z_][A-Za-z0-9_]*\b'
    r'(?=.*[_0-9A-Z])'
)

PATH_RE = re.compile(r'(?:(?:~|/)[^\s]+)|(?:[A-Za-z]:\\[^\s]+)')
FLAG_RE = re.compile(r'\B--?[A-Za-z][A-Za-z0-9-]*\b')

# --- Safe spacing rules ---
MULTISPACE_RE = re.compile(r'[ \t]{2,}')
SPACE_BEFORE_PUNCT_RE = re.compile(r'\s+([,.;:!?])')
SPACE_AFTER_PUNCT_RE = re.compile(r'([,.;:!?])([A-Za-z0-9])')
ELLIPSIS_RE = re.compile(r'\.\s*\.\s*\.')
SPACE_AFTER_DOT_RE = re.compile(r'(\.)([A-Za-z])')  # catches "spaces.after"

# --- Dot-joined word fix ---
DOMAIN_LIKE_RE = re.compile(
    r'\b[A-Za-z0-9-]+\.(?:com|net|org|io|co|ai|app|dev|gov|edu|me|gg|tv|fm|hk|tw|jp|sg|kr|cn|uk|de|fr|it|es|nl|se|no|fi)\b',
    re.IGNORECASE
)
IP_RE = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
VERSION_RE = re.compile(r'\b\d+(?:\.\d+){1,}\b')
ABBREV_RE = re.compile(r'\b(?:[A-Za-z]\.){2,}\b')  # U.S.A.

# Prose dot joins (now allows initial caps too), e.g. "sentence.with" -> "sentence with"
PROSE_DOT_JOIN_RE = re.compile(r'(?<!\w)([A-Za-z]{2,})\.([A-Za-z]{2,})(?!\w)')

PLACEHOLDER_FMT = "\uE000{n}\uE000"

def protect(text: str) -> Tuple[str, Dict[str, str]]:
    protected: Dict[str, str] = {}
    n = 0

    def sub(pat: re.Pattern, s: str) -> str:
        nonlocal n
        def repl(m: re.Match) -> str:
            nonlocal n
            key = PLACEHOLDER_FMT.format(n=n)
            n += 1
            protected[key] = m.group(0)
            return key
        return pat.sub(repl, s)

    # Protect brand tokens first so they never get split/recased
    text = sub(BRAND_RE, text)

    # Then protect the usual “never touch” stuff
    for pat in (URL_RE, EMAIL_RE, PATH_RE, FLAG_RE, DOT_IDENT_RE, CAMEL_RE, SNAKE_RE, KEBAB_RE):
        text = sub(pat, text)

    return text, protected

def unprotect(text: str, protected: Dict[str, str]) -> str:
    for k, v in protected.items():
        text = text.replace(k, v)
    return text

def fix_dot_joined_words(text: str) -> str:
    """
    iPhone-like: split dot-joined prose words, but never domains/IPs/versions/abbrev.
    Operates AFTER protection, so URLs/emails/camelCase/etc are already safe.
    """
    # Repeatedly split word.word into word word (handles dot.joined.words)
    for _ in range(8):
        text = PROSE_DOT_JOIN_RE.sub(r"\1 \2", text)

    return text

def safe_spacing_cleanup(text: str) -> str:
    text = ELLIPSIS_RE.sub("...", text)
    text = SPACE_BEFORE_PUNCT_RE.sub(r"\1", text)
    text = SPACE_AFTER_PUNCT_RE.sub(r"\1 \2", text)
    text = SPACE_AFTER_DOT_RE.sub(r"\1 \2", text)
    text = MULTISPACE_RE.sub(" ", text)
    return text

def iphone_like_caps(text: str) -> str:
    """
    Light phone-style caps:
    - Standalone "i" -> "I"
    - Capitalize after ". " / "! " / "? "
    - Capitalize first alpha of each paragraph
    """
    text = re.sub(r'(?<![A-Za-z])i(?![A-Za-z])', 'I', text)

    def cap_after_punct(m: re.Match) -> str:
        return m.group(1) + m.group(2) + m.group(3).upper()
    text = re.sub(r'([.!?])(\s+)([a-z])', cap_after_punct, text)

    def cap_para(m: re.Match) -> str:
        return m.group(1) + m.group(2).upper()
    text = re.sub(r'(^|\n\s*\n)([a-z])', cap_para, text)

    return text

def call_lt(text: str, session: requests.Session) -> dict:
    data = {"language": LANG, "text": text}
    r = session.post(LT_URL, data=data, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def apply_misspellings_only(text: str, matches: List[dict]) -> str:
    shift = 0
    for m in matches:
        rule = m.get("rule", {})
        if rule.get("issueType") != "misspelling":
            continue
        repls = m.get("replacements") or []
        if not repls:
            continue

        start = m["offset"] + shift
        end = start + m["length"]
        replacement = repls[0]["value"]

        # Don’t touch protected placeholders
        if "\uE000" in text[start:end]:
            continue

        orig = text[start:end]

        # Skip pure capitalization swaps (avoid “English teacher mode”)
        if orig.lower() == replacement.lower() and orig != replacement:
            continue

        text = text[:start] + replacement + text[end:]
        shift += len(replacement) - m["length"]
    return text

def chunk_paragraphs(text: str) -> List[str]:
    parts = re.split(r'(\n\s*\n)', text)
    chunks: List[str] = []
    cur = ""
    for p in parts:
        if len(cur) + len(p) > MAX_CHUNK_CHARS and cur:
            chunks.append(cur)
            cur = ""
        cur += p
    if cur:
        chunks.append(cur)
    return chunks

def normalize_brands(text: str) -> str:
    for b in BRANDS:
        text = re.sub(r'\b' + re.escape(b) + r'\b', b, text, flags=re.IGNORECASE)
    return text

def main() -> int:
    raw = ""
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
    if not raw and len(sys.argv) > 1:
        raw = " ".join(sys.argv[1:])
    if not raw.strip():
        return 0

    safe, protected = protect(raw)

    # Fast local "phone-like" cleanup first
    safe = fix_dot_joined_words(safe)
    safe = safe_spacing_cleanup(safe)
    safe = iphone_like_caps(safe)

    chunks = chunk_paragraphs(safe) if len(safe) > MAX_CHUNK_CHARS else [safe]

    with requests.Session() as s:
        s.headers.update({"Connection": "keep-alive"})
        out_chunks = []
        for ch in chunks:
            try:
                resp = call_lt(ch, s)
                ch = apply_misspellings_only(ch, resp.get("matches", []))
            except Exception as e:
                print(f"[SpellFix error] {e}", file=sys.stderr)
            out_chunks.append(ch)

    out = "".join(out_chunks)
    out = unprotect(out, protected)
    out = normalize_brands(out)

    sys.stdout.write(out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
