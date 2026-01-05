# SpellFix

SpellFix is a fast, local, *safe* autocorrect script inspired by iPhone typing behavior.

It fixes spelling, spacing, and punctuation **without rewriting tone** and **without breaking**:
- URLs
- emails
- camelCase variables
- code-like text

## What it does
- Fixes common misspellings
- Cleans spacing and punctuation
- Fixes dot-joined words in normal prose
- Preserves technical text
- Runs locally (privacy-friendly)

## What it does NOT do
- No grammar rewriting
- No style enforcement
- No “English teacher” behavior

## Requirements
- Python 3
- Local LanguageTool server
- (Optional) Alfred for hotkey usage

## Usage

SpellFix is designed to be used as a command-line or hotkey-triggered script.

### Basic usage
Clean text from a file:
```bash
python spellfix.py < input.txt
