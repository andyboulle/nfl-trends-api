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

## Environment Setup

This application uses separate environment files for development and production environments.

### Development Environment

1. Create a `.env.dev` file for development variables
    ```bash
    touch .env.dev
    ```

2. Populate your `.env.dev` file with your local database configuration
    ```env
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=nfl-trends-dev
    DB_USER=postgres
    DB_PASSWORD=password
    ```

### Production Environment

1. Create a `.env.prod` file for production variables
    ```bash
    touch .env.prod
    ```

2. Populate your `.env.prod` file with your production database configuration
    ```env
    DB_HOST=your-prod-host
    DB_PORT=5432
    DB_NAME=nfl-trends-prod
    DB_USER=your-prod-user
    DB_PASSWORD=your-prod-password
    ```

### Environment File Loading

The application loads the appropriate environment file based on the `ENV` environment variable:
- `ENV=dev` → loads `.env.dev`
- `ENV=prod` → loads `.env.prod`

## Execution

### Development Mode
Start the API server in development mode (uses `.env.dev`):
```bash
export ENV=dev && uvicorn app.main:app --reload
```

### Production Mode

Start the API server in production mode (uses `.env.prod`):

```bash
export ENV=prod && uvicorn app.main:app
```

**Note:** The --reload flag is omitted in production for better performance and security.

## API Documentation

Once the server is running, you can access:

- **Interactive API documentation**: http://localhost:8000/docs
- **Alternative documentation**: http://localhost:8000/redoc

## Development

The API provides endpoints for:

- NFL game data and results
- Historical betting trends analysis
- Upcoming games with current lines
- Email subscription management
- Filtering and pagination capabilities

For detailed endpoint documentation and model schemas, refer to the docs folder or visit the interactive documentation when the server is running.