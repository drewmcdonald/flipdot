# Flipdot Display Controller

A web interface and controller for flipdot displays.

## Features

*   Web interface for controlling the display and selecting modes.
*   Support for various display modes (e.g., Clock, Solid Colors, custom text).
*   Extensible architecture for adding new display modes and fonts.
*   Structured logging in JSON format for easier parsing and monitoring.
*   Comprehensive unit tests using `pytest`.
*   Command-line interface for starting the server.

## Prerequisites

*   Python 3.10+
*   Poetry (for dependency management and running scripts)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd flipdot-controller # Or your repository directory name
    ```

2.  **Install dependencies using Poetry:**
    ```bash
    poetry install
    ```

## Running the Application

The application server can be run using the `flipdot-server` command, which is an entry point defined in `pyproject.toml`.

```bash
poetry run flipdot-server [OPTIONS]
```

**Common Options:**

*   `--layout TEXT`: JSON string defining the panel layout (e.g., `'[[1], [2]]'`).
    Default: `'[[1], [2]]'`
*   `--device TEXT`: Path to the serial device (e.g., `/dev/ttyUSB0`). If not provided, the server may run in a simulated mode or without hardware interaction depending on its configuration.
*   `--baudrate INTEGER`: Serial port baud rate. Default: `57600`
*   `--host TEXT`: Host address to bind the server to. Default: `0.0.0.0`
*   `--port INTEGER`: Port to run the server on. Default: `8080`
*   `--dev`: Enable development mode. This typically enables features like hot reloading and may print display content to the console if no serial device is connected.

**Example:**

To run in development mode without a physical device:
```bash
poetry run flipdot-server --dev
```

To run with a specific device:
```bash
poetry run flipdot-server --device /dev/ttyUSB0 --layout '[[1,2,3],[4,5,6]]'
```

Alternatively, you can directly invoke the server script:
```bash
poetry run python flipdot/cli/server.py --dev
```

## Running Tests

The project uses `pytest` for unit testing. To run all tests:

```bash
poetry run pytest
```
Or to specify the tests directory:
```bash
poetry run pytest tests/
```

## Development

This project uses several tools to ensure code quality:

*   **Ruff**: For linting and formatting.
    ```bash
    poetry run ruff check .
    poetry run ruff format .
    ```
*   **MyPy**: For static type checking.
    ```bash
    poetry run mypy flipdot/ tests/ flipdot/cli/server.py
    ```
    (Note: `server.py` was moved to `flipdot/cli/server.py`. The main `server.py` in the root was removed.)

The project is configured with GitHub Actions to run these checks automatically on push and pull requests.
