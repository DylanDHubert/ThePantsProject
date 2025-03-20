# ThePantsProject Development Guidelines

## Build and Run Commands
- `poetry install` - Install dependencies
- `poetry run python manage.py migrate` - Run migrations
- `poetry run python manage.py makemigrations` - Generate migrations
- `poetry run python manage.py runserver` - Start server (use localhost:8000, not 127.0.0.1:8000)
- `poetry run python manage.py test server.tests` - Run all tests
- `poetry run python manage.py test server.tests.TestClass.test_method` - Run specific test

## Code Style Guidelines
- **Formatting**: Follow PEP 8 conventions for Python code
- **Imports**: Group imports in order: standard library, third-party, local application
- **Naming**: snake_case for variables/functions, CamelCase for classes, UPPER_CASE for constants
- **Django**: Follow Django's MTV (Model-Template-View) architecture
- **JavaScript**: Use camelCase for variables/functions, organize by feature/component
- **Error Handling**: Use try/except for API calls and file operations, return appropriate HTTP responses
- **Comments**: Document complex algorithms, especially in latent space and GAN implementations
- **Type Hints**: Use Python type hints for function parameters and return values

## Data Processing Commands
- `poetry run python manage.py csv` - Import data from CSV files
- `poetry run python manage.py rtree` - Create spatial index for pants database