# User Uploads Directory

After cloning the project, place your custom data files here. The system will
automatically detect them and make them available in the WebUI.

## Directory Structure

```
data/uploads/
├── datasets/          # JSONL dataset files
│   ├── my_exam.jsonl
│   └── my_image_quiz.jsonl
├── images/            # Image files for image_mcq tasks
│   ├── photo1.jpg
│   ├── photo2.png
│   └── diagrams/
│       └── chart.png
└── README.md
```

## How to Use

### 1. Add Dataset Files

Put your `.jsonl` files into `data/uploads/datasets/`. Each line must be a valid
JSON object following the AgentInferKit schema. Example for `image_mcq`:

```json
{"sample_id": "q001", "task_type": "image_mcq", "question": "What animal is shown?", "options": {"A": "Cat", "B": "Dog", "C": "Bird", "D": "Fish"}, "answer": "B", "image_url": "uploads://images/photo1.jpg", "difficulty": "easy", "metadata": {"topic": "animals"}}
```

### 2. Add Image Files

Put image files (`.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`) into
`data/uploads/images/`. Subdirectories are supported.

### 3. Reference Images in Datasets

In your JSONL dataset, reference local images using the `uploads://` scheme:

- `"image_url": "uploads://images/photo1.jpg"` — resolves to `data/uploads/images/photo1.jpg`
- `"image_url": "uploads://images/diagrams/chart.png"` — subdirectory supported
- `"image_url": "https://example.com/img.jpg"` — remote URLs still work

### 4. Auto-Discovery

When the server starts (or when you call `POST /api/v1/uploads/scan`), all
datasets in this directory are automatically registered and appear in the WebUI
dataset selector. Images are listed via `GET /api/v1/uploads/images`.

## Supported Formats

- **Datasets**: `.jsonl` only
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.bmp`, `.svg`
