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

## CI/CD

Every push to `main` that touches this project triggers a GitHub Actions
workflow which builds the Docker image and publishes it to Docker Hub,
tagged with both `latest` and the commit SHA. Pull requests build the
image without publishing, so changes are verified before merge.

## Deployment

Requirement #2 is implemented against a locally simulated server:
Terraform provisions an SSH-accessible Ubuntu container, and Ansible
configures it — installing Docker, pulling the published image from
Docker Hub, and running the stack with docker-compose.

The deploy step is run manually (`ansible-playbook -i inventory.ini
playbook.yml`) rather than from CI, because this repository is public and
deploying to a local machine would require a self-hosted runner, which is
a security risk on public repositories.

Moving to a real cloud server requires changing the Terraform provider
block and the Ansible inventory host. The playbook itself is unchanged.
