# Multi-Container Todo API

A todo list API running as a multi-container application with Docker Compose:
a Node.js/Express service backed by MongoDB.

https://roadmap.sh/projects/multi-container-service

## Endpoints

| Method | Path         | Description          |
| ------ | ------------ | -------------------- |
| GET    | `/todos`     | List all todos       |
| POST   | `/todos`     | Create a todo        |
| GET    | `/todos/:id` | Get a todo by id     |
| PUT    | `/todos/:id` | Update a todo by id  |
| DELETE | `/todos/:id` | Delete a todo by id  |

## Running locally

```bash
docker compose up --build
```

The API is available at http://localhost:3000. Todo data is persisted in a
named Docker volume, so it survives stopping and starting the containers.
