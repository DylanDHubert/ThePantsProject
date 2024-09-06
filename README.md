# The Pants Project

## Project Structure
- `server/`: Django server
- `process/`: Django process service
- `pyproject.toml`: Poetry dependency management
- `docker-compose.yml`: Docker configuration

## Setup

### Prerequisites
- Python 3.9+
- Poetry
- Docker and Docker Compose (optional)

### Local Development

1. Install dependencies:
    poetry install

2. Run server:
    cd server
    poetry run python manage.py runserver
    
### Docker Development
1. Build and start services:
    docker-compose up --build

## Project Evolution

1. Migrated from Flask to Django for both server and process services.
- Reason: Django provides a more robust framework for larger applications. Also some experience.

2. Implemented Poetry for dependency management.
- Reason: Ensures consistent environments across development machines.

3. Maintained Docker setup for containerization.
- Reason: Facilitates consistent deployment and scaling.

## Notes

- Use Poetry for running Django commands and managing dependencies.
- Docker setup allows for isolated, reproducible environments.
- `pyproject.toml` at root manages dependencies for both services.
