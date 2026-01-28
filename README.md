# Plana.AI Backend

AI-powered planning intelligence platform for UK planning applications.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/henrypygall05-byte/plana-ai-backend.git
cd plana-ai-backend

# Install (no dependencies required)
pip install -e .

# Initialize
plana init

# List demo applications
plana demo

# Process an application
plana process 2024/0930/01/DET
```

That's it! No API keys, databases, or external services needed.

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
