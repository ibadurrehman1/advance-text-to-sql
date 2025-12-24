# Advance Text to SQL

Production-ready Advanced Text to SQL Agent using LangChain. A FastAPI-based application that converts natural language queries into SQL statements.

## System Architecture

### Architecture Layers

1. **API Layer** (`app/api/`): Handles HTTP requests and responses, defines routes
2. **Controllers** (`app/controllers/`): Process HTTP requests and format responses
3. **Services** (`app/services/`): Contains business logic and core functionality
4. **Repositories** (`app/repositories/`): Abstracts database operations
5. **Schemas** (`app/schemas/`): Pydantic models for request/response validation

### Middleware Stack

The application uses the following middleware (in order):

1. **CORS Middleware**: Handles cross-origin requests
2. **Trusted Host Middleware**: Validates allowed hosts
3. **GZip Middleware**: Compresses responses
4. **Sentry Context Middleware**: Adds Sentry context (if enabled)
5. **Request Logging Middleware**: Logs all requests with details
6. **Response Time Middleware**: Tracks and logs response times
7. **Rate Limit Middleware**: Enforces rate limits per client (if enabled)
8. **Request ID Middleware**: Adds unique request IDs to all requests

### Database

The application uses **MongoDB** with **Motor** (async MongoDB driver). The database connection is managed through the `MongoDBConnector` class, which handles connection pooling and lifecycle management.

### Key Features

- **FastAPI**: High-performance async API framework
- **MongoDB**: Async database connectivity using Motor
- **JWT Authentication**: Token-based authentication system
- **Rate Limiting**: Configurable per-client rate limits
- **Structured Logging**: JSON-formatted logging with file rotation
- **Sentry Integration**: Error tracking and performance monitoring
- **Request Tracking**: Unique request IDs for tracing
- **Security Middleware**: CORS, trusted hosts, security headers

## How to Run

### Prerequisites

- Python 3.12 or higher
- MongoDB instance (local or remote)
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

### Installation

#### Using uv (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd advance-text-to-sql

# Install dependencies
uv sync

# Install development dependencies (optional)
uv sync --extra dev
```

#### Using pip

```bash
# Clone the repository
git clone <repository-url>
cd advance-text-to-sql

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -e ".[dev]"  # Optional: for development
```

### Running the Application

#### Development Mode

```bash
# Using uv
uv run python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access Points

Once running, the application is available at:

- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health

## Author

**Ibad ur Rehman**
Email: ibadurrehman4077@gmail.com
