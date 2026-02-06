# AGENTS

This document defines repository-specific guidance for AI agents working on this project.

## Project Overview
AutoCase is a CLI tool that uses an LLM to generate standardized test cases from YAML input and outputs a formatted Excel/CSV file.

## Key Commands
- Install (editable): `pip3 install -e .`
- Run (default): `autocase -f input.example.yaml`
- JSON only: `autocase -f input.example.yaml --json-only`
- Help: `autocase -h`

## Inputs / Outputs
- Default input directory: `inputs/`
- Default output directory: `outputs/`
- If `-o` is omitted, output is `{input}_{timestamp}_testcases.xlsx` in `outputs/`.

## Configuration Files
- LLM config: `config/llm.yaml` (local only; use `config/llm.example.yaml` as template)
- System prompt: `config/system_prompt.txt`

## Output Contract
The LLM must return a JSON array of objects with these fields:
- `type`
- `name`
- `priority`
- `pre`
- `steps`
- `expected`
- `stage`

The tool adds IDs, module, and keywords automatically.

## Coding Conventions
- Prefer explicit error messages and non-zero exit codes.
- Keep CLI behavior stable; `autocase` with no args prints banner + help.
- Use ASCII-only edits unless the file already contains non-ASCII.

## Testing Notes
There are no automated tests currently. Manual checks:
- Run `autocase -f inputs/input.example.yaml` (requires API key).
- Run `autocase -f inputs/input.example.yaml --json-only`.

## Review Checklist
- CLI flags work as documented.
- Output Excel formatting remains intact.
- CSV output works and columns are ordered correctly.
- LLM config and prompt are loaded correctly.
- Default input/output directory logic still works.
