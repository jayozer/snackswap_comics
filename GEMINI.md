# SnackSwap Comics

## Project Overview

SnackSwap Comics is an AI-powered progressive web app that transforms a simple photo of a snack or lunch into an engaging 4-panel comic where foods become characters debating tooth health. The backend is a Python FastAPI application that uses Google Gemini for vision detection and script generation, and Qdrant as a vector database for fact retrieval. The frontend is a planned Next.js/React PWA.

## Building and Running

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Qdrant server (local or cloud)
- Google Gemini API key

### Installation & Setup

1.  **Clone the repository**
2.  **Set up the backend:**
    ```bash
    cd backend
    uv venv
    source .venv/bin/activate
    uv pip install -r requirements.txt
    ```
3.  **Configure environment:**
    ```bash
    cp .env.example .env
    # Edit .env and add your API keys
    ```
4.  **Start Qdrant (if running locally):**
    ```bash
    docker run -p 6333:6333 qdrant/qdrant
    ```
5.  **Seed the database:**
    ```bash
    ./seed_data.sh
    ```
6.  **Run the server:**
    ```bash
    ./run_server.sh
    ```
    The server will be available at `http://localhost:8000` and the API documentation at `http://localhost:8000/docs`.

## Development Conventions

The project uses `black` for code formatting and `ruff` for linting. The configuration for these tools can be found in the `pyproject.toml` file. The project also uses `mypy` for static type checking.
