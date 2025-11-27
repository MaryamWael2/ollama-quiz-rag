# ollama-quiz-rag

A small Retrieval-Augmented Generation (RAG) prototype that uses **Ollama** to generate **quiz questions from your own documents**.

The project lets you:

- Load local documents
- Build a vector index over their contents
- Query them via a local LLM served by Ollama
- Generate quiz-style questions based on the retrieved context
- Experiment interactively via a UI or CLI

## Features

The project lets you:

- 🧠 **Local LLM via Ollama** – run everything on your own machine, no external APIs required.
- 📄 **Document ingestion** – read and preprocess documents.
- 🔍 **RAG pipeline** – retrieve relevant chunks from your corpus and pass them to an Ollama model.
- ❓ **Quiz generation** – generate question/answer pairs from your documents.
- 💻 **CLI & UI** – use the command-line interface (`CLI.py`) or the UI (`UI.py`).

## Project Structure

```text
.
├── CLI.py               # Command-line entry point
├── UI.py               # UI application entry point
├── DocumentsReader.py   # Utilities for reading and chunking documents
├── RAG.py               # Core RAG + quiz generation logic
├── requirements.txt     # Python dependencies
└── Notebook Example/    # Document + Jupyter notebook example
````

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/MaryamWael2/ollama-quiz-rag.git
cd ollama-quiz-rag
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Install ollama using the command below or install from the official site: https://ollama.com/download**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

4. **Start the Ollama server (if not already running)**

```bash
ollama serve
```

5. **Pull at least one model from Ollama (depending on your computational power)**

```bash
ollama pull MODEL_NAME
```
Example:
```bash
ollama pull llama3:8b
```

## Usage

### 1. Command-Line Interface

The CLI script is in `CLI.py`.

```bash
python CLI.py
```

### 2. User Interface

To run the user interface run the following command in the terminal.

```bash
python UI.py
```

## Contributing / Next Steps

Ideas to extend this project:

* Add support for more document types (HTML, markdown, etc.)
* Improve quiz formats (multiple choice with distractors, true/false, etc.)

Pull requests and issues are welcome.
