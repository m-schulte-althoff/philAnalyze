# philAnalyze

A philosophical text analysis tool with Model-View-Controller architecture for analyzing ODT documents and exporting to Obsidian.

## Project Structure

```
philAnalyze/
├── main.py                 # Main entry point and pipeline orchestration (Controller)
├── data_model.py          # Data loading and preprocessing (Model)
├── views.py               # Visualization and reporting (View)
├── obsidian_export.py     # Obsidian markdown export functionality
├── data/                  # Input data directory
│   └── Phil.odt          # Philosophical text data
├── output/               # Generated outputs (plots, exports)
├── tests/                # Unit tests
│   ├── test_main.py
│   ├── test_data_model.py
│   ├── test_views.py
│   └── test_obsidian_export.py
├── pyproject.toml        # Project dependencies and Python version
├── uv.lock               # Locked dependency versions
├── .pylintrc            # Pylint configuration
└── README.md            # This file
```

## Features

- **ODT File Loading**: Parse OpenDocument Text files and extract structured content
- **Data Visualization**: Generate exploratory visualizations of text data
- **Obsidian Export**: Transform data into Obsidian-compatible markdown format (placeholder)
- **Modular Architecture**: Clean MVC separation for maintainability
- **Comprehensive Testing**: Full pytest test suite with >90% coverage goal

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd philAnalyze
```

2. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if it is not already available.

3. Create the project environment and install the locked dependencies:
```bash
uv sync
```

`uv sync` creates and maintains the local `.venv` environment. Run all project commands through `uv run`; it automatically keeps that environment synchronized with `uv.lock`.

## Usage

### Running the Analysis

Run the main pipeline:
```bash
uv run python main.py
```

### Configuration

Edit the configuration flags at the top of `main.py`:

```python
USE_VISUALIZATIONS = True    # Generate exploratory plots
EXPORT_TO_OBSIDIAN = False   # Export to Obsidian format (currently placeholder)
DATA_PATH = 'data/Phil.odt'  # Input data file
```

### Running Tests

Run all tests:
```bash
uv run pytest
```

Run with coverage report:
```bash
uv run pytest --cov=. --cov-report=html
```

Run specific test file:
```bash
uv run pytest tests/test_data_model.py
```

### Code Quality

Run pylint:
```bash
uv run pylint main.py data_model.py views.py obsidian_export.py
```

Format code with black:
```bash
uv run black .
```

## Module Descriptions

### main.py (Controller)
Main orchestration module that:
- Coordinates the analysis pipeline
- Manages configuration flags
- Handles module integration
- Provides logging

### data_model.py (Model)
Data handling module that:
- Loads ODT files using odfdo library
- Extracts text and metadata
- Preprocesses and cleans data
- Calculates text statistics
- Exports to CSV

### views.py (View)
Visualization module that:
- Creates exploratory plots
- Generates text length distributions
- Produces content statistics visualizations
- Creates summary reports

### obsidian_export.py
Export module that:
- Transforms data to Obsidian markdown format
- Creates YAML frontmatter
- Generates wikilink-style connections (placeholder)
- Sanitizes filenames

## Development Status

### Completed
- ✅ MVC architecture setup
- ✅ ODT file loading
- ✅ Data preprocessing
- ✅ Basic visualizations
- ✅ Test suite structure
- ✅ Pylint configuration

### In Progress / TODO
- 🔄 Obsidian export implementation (currently placeholder)
- 🔄 Advanced text analysis features
- 🔄 Enhanced link extraction
- 🔄 Section-based export

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) for dependency and environment management
- pandas >= 2.0.0, < 3.0.0
- matplotlib >= 3.7.0
- odfdo >= 3.6.0
- pytest >= 7.4.0
- pylint >= 3.0.0

## License

[Add your license information here]

## Contributing

1. Synchronize dependencies: `uv sync`
2. Ensure all tests pass: `uv run pytest`
3. Check code quality: `uv run pylint <files>`
4. Format code: `uv run black .`
5. Add tests for new features
6. Update documentation

## Architecture Notes

This project follows a Model-View-Controller pattern inspired by the AlboConservative repository:

- **Model** (data_model.py): Handles all data operations
- **View** (views.py): Handles all visualization and presentation
- **Controller** (main.py): Orchestrates the pipeline and coordinates modules

The architecture ensures:
- Separation of concerns
- Easy testing and mocking
- Modular feature development
- Clear data flow
