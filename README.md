# NFL Trends API

This repository starts an API server that provides information about NFL games and trends since the start of the 2006-2007 season.

Information about the endpoints and models used can be found in the `docs/` folder.

## Prerequisites

- Python
- PostgreSQL

## Installation

1. Clone the repository
    ```bash
    git clone https://github.com/andyboulle/nfl-trends-api.git
    ```

2. Navigate to the directory
    ```bash
    cd nfl-trends-api 
    ```

3. Create a virtual environment
    ```bash
    python3 -m venv .venv
    ```

4. Activate the virtual environment
    ```bash
    source .venv/bin/activate
    ```

5. Install dependencies
    ```bash
    pip install -r requirements.txt
    ```

## Setup

1. Create a `.env` file for environment variables
    ```bash
    touch .env
    ```

2. Populate your `.env` file with your database configurations
    ```python
    DB_HOST=
    DB_PORT=
    DB_NAME=
    DB_USER=
    DB_PASSWORD=
    ```

    _EXAMPLE:_
    ```python
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=nfl-trends
    DB_USER=postgres
    DB_PASSWORD=password
    ```

## Execution

1. Start the API server
    ```bash
    uvicorn app.main:app --reload
    ```
