# Plana.AI Backend

AI-powered planning intelligence platform for UK planning applications.

## Quick Start

```bash
python -m venv venv
source venv/bin/activate
pip install -e .
plana init
plana demo
plana process 2024/0930/01/DET
```

## Available Commands

```bash
plana --help              # Show help
plana init                # Initialize the system
plana demo                # List available demo applications
plana process <ref>       # Process a planning application
```

## Demo Applications

| Reference | Description |
|-----------|-------------|
| `2024/0930/01/DET` | T J Hughes extension (Conservation Area) |
| `2024/0943/01/LBC` | T J Hughes listed building consent |
| `2024/0300/01/LBC` | Grainger Street shopfront |
| `2025/0015/01/DET` | Town Moor drainage |
| `2023/1500/01/HOU` | Jesmond Road householder |

## Requirements

- Python 3.11+

## License

MIT License - see [LICENSE](LICENSE) for details.
