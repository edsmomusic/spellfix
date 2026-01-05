````md
# SpellFix

SpellFix is a fast, local, *safe* autocorrect script inspired by iPhone typing behavior.

It fixes spelling, spacing, and punctuation **without rewriting tone** and **without breaking**:
- URLs
- emails
- camelCase variables
- code-like text

---

## ⚡ Quick Start

```bash
# Make sure your local LanguageTool server is running
python spellfix.py < input.txt
````

SpellFix reads text from **stdin** and outputs corrected text to **stdout**.

---

## Example

**Input**

```
im writinganother sentence.thishas weird spacing,wrong punctuation,and URLs like https://example.com/testPage
```

**Output**

```
I'm writing another sentence. This has weird spacing, wrong punctuation, and URLs like https://example.com/testPage
```

---

## What it does

* Fixes common misspellings
* Cleans spacing and punctuation
* Fixes dot-joined words in normal prose
* Preserves technical text
* Runs locally (privacy-friendly)

---

## What it does NOT do

* No grammar rewriting
* No style enforcement
* No “English teacher” behavior
* No cloud or AI rewriting

---

## Why SpellFix?

Most grammar tools:

* rewrite your tone
* overcorrect casual writing
* break URLs, emails, or code
* require cloud access

SpellFix behaves like a **smartphone keyboard**:
helpful, fast, and invisible.

---

## Requirements

* Python 3
* Local LanguageTool server
* (Optional) Alfred for hotkey usage

---

## Usage

SpellFix is designed to be used as a command-line or hotkey-triggered script.

### Basic usage

Clean text from a file:

```bash
python spellfix.py < input.txt > output.txt
```

Pipe from another command:

```bash
cat input.txt | python spellfix.py
```

---

## Limitations

* Does not understand context
* Does not rewrite sentences
* Does not fix complex grammar issues

SpellFix is intentionally minimal.

---

## Roadmap

* [ ] Optional capitalization fixes
* [ ] Optional punctuation spacing mode
* [ ] Alfred workflow
* [ ] Simple macOS app wrapper

```
```
