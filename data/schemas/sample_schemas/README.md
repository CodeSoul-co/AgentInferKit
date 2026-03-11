# Sample Schemas

JSON Schema definitions for all benchmark sample types, as specified in `method.md` §5.3.

## Schema Files

| File | Task Type | Description |
|------|-----------|-------------|
| `universal.json` | (base) | Universal fields shared by all samples |
| `qa.json` | `qa` | Open-domain question answering |
| `text_exam.json` | `text_exam` | Text-based multiple-choice examination |
| `image_mcq.json` | `image_mcq` | Image understanding multiple-choice |
| `api_calling.json` | `api_calling` | Agent API function calling |

## Data Version Stages

As defined in `method.md` §5.3.3:

1. **raw** — Original source data (`data/raw/`)
2. **cleaned** — After cleaning and deduplication (`data/cleaned/`)
3. **processed** — After transformation and enrichment (`data/processed/`)
4. **benchmark_release** — Final version used in experiments (`data/benchmark/`)

Use the `version` field in each sample to track which stage the data is at.

## Mapping Files

Located in `data/mappings/`:

- `qa_to_chunk/` — QA sample ID to knowledge chunk ID mapping
- `exam_to_chunk/` — Text-exam question to knowledge chunk mapping
- `image_desc_to_mcq/` — Original image description to MCQ mapping
