# WordleWise (backend)

This is the backend for WordleWise, an app used by myself and my wife to keep track of our Wordle scores. It's built with Flask and provides an API for the React frontend.

## API endpoints
- `/login`: authenticate users
- `/getScores`: retrieve weekly and daily score data
- `/addScore`: add new scores
- `/getUsers`: get user information
- `/executeSql`: (admin only) run SQL commands on the database

## Database
The app uses SQLite for data storage. The database schema includes:

- **User table**: stores user information
- **Score table**: stores Wordle scores with date and user relationships

The database file is stored in a volume on the server to persist data between container restarts.

## Running the app locally
The simplest way to run the app locally is using Docker.

1. Ensure you have git, Docker and Docker Compose installed
2. Clone this repository
3. Create an `.env` file based on `.env.example` and add a value for the `JWT_SECRET_KEY` parameter. You can generate a key using a command like `python -c "import secrets; print(secrets.token_hex(13))"`
4. Copy a backup of the production SQLite database `wordlewise.db` into the root of the repo
5. Run `docker compose up -d`
6. The app will be available to serve requests from the [frontend](https://github.com/wjrm500/WordleWise-frontend) on port 5000

You can also run the app without Docker. You'll need Python and can use [uv](https://docs.astral.sh/uv/) to do this. Follow steps 2 to 4 above but then for step 5, run `uv run main.py`.

## Deploying the app
This app is currently deployed as a Docker container on a DigitalOcean Droplet, alongside various other containerised apps. These containerised apps are managed through the [ServerConfig](https://github.com/wjrm500/ServerConfig) repository, which includes a variety of Docker Compose configurations that reference Docker images stored on Docker Hub. Thus, to deploy any new code changes, we need to (A) build the image locally, (B) push the image up to Docker Hub, (C) SSH into the Droplet, (D) pull the image, and (E) restart the container.

Locally...

(A) Build the image:
```bash
docker build -t wjrm500/wordlewise-backend:latest .
```

(B) Push the image:
```bash
docker login
docker push wjrm500/wordlewise-backend:latest
```

On the remote server...

(D) Pull the image:
```bash
docker compose -p wordlewise -f /home/ServerConfig/wordlewise-docker-compose.yml pull
```

(E) Restart the container:
```bash
docker compose -p wordlewise -f /home/ServerConfig/wordlewise-docker-compose.yml up -d
```