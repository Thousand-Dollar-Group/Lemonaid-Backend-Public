# 🍋 Lemonaid-RAG-Agents

This is the backend **RAG (Retrieval-Augmented Generation)** system for Lemonaid, powered by vector search, the Gemini API, and Hugging Face MiniLM.
It enables powerful, context-aware AI agents for chatbots, image queries, and summarization.

---

## 🚀 Quickstart: Running the Server

Follow these four simple steps to get the entire RAG system and chatbot server running with Docker.

### 1 · Setup Environment and Prepare Data

Before building the Docker containers, configure your API keys and place your data files.

0. **Prerequisites**
   Before you begin, ensure you have the following tools installed on your system:

   1.  **Git:** To clone the repository.
   2.  **Docker & Docker Compose:** To build and run the application containers.
   3.  **AWS CLI:** Required for configuring credentials and downloading environment files.
      * **macOS:** `brew install awscli`
      * **Linux/Other:** [Official AWS CLI Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

1. **Clone the repository**

   ```bash
   git clone [your-repo-link]
   cd Lemonaid-RAG-Agents
   ```

2. **Prepare your CSV data**

   Place any CSV files to be ingested into the vector database inside `src/data/`.
   The ingestion script automatically scans this directory.

---

### 2 · Build, Run, and Ingest

   This script automates the entire setup, including AWS configuration, environment file download, and Docker startup.

   ```bash
   ./setup.sh
   ```

   > **What does this script do?**
   > * Checks if the AWS CLI is installed.
   > * Asks you to configure your AWS credentials (Access Key, Secret Key, and Region) if they aren't found.
   > * Downloads the production `.env` file from the S3 bucket.
   > * Stops and removes any old Docker containers and volumes.
   > * Builds new Docker images (`--no-cache`).
   > * Starts all services using `docker-compose`.

> 💡 Tip: If you don’t run in detached mode, Docker will stream the logs in your terminal.
> Press Ctrl +C to gracefully stop all running containers when you’re done.

---

### 3 · Verify Database Content (Recommended)

1. **Enter the PostgreSQL container**

   ```bash
   docker exec -it pgvector-db psql -U postgres -d vectordb
   ```

2. **Inspect the database**

   ```sql
   \d
   SELECT * FROM documents LIMIT 5;
   \q
   ```

---

## 🛠️ Common Operations

### Restart all containers

Use after editing `.env` or configuration files so containers reload environment variables.

```bash
docker-compose -f ./docker/docker-compose.yml up --force-recreate
```
> 💡 Tip: To run Docker in detached mode (in the background), add `-d` to the command, e.g., `docker-compose ... up -d`.

### Stop all containers

Press Ctrl + C if running in the foreground,
or stop and remove containers explicitly:

```bash
docker-compose -f ./docker/docker-compose.yml down
```

### Rebuild all containers (when dependencies change)

Run these when you modify dependencies or the Dockerfile.
This rebuilds the **images** from scratch, then recreates containers from those new images.

```bash
# Rebuild images without using cached layers
docker-compose -f ./docker/docker-compose.yml build --no-cache

# Recreate containers with the new images
docker-compose -f ./docker/docker-compose.yml up --force-recreate
```

*(Omit `--no-cache` for faster incremental builds when dependencies haven’t changed.)*

---

## 📝 Important Notes

* Vector search quality depends on the **embedding model format** and the **pgvector index**.
  Verify that your data is properly structured and indexed for efficient retrieval.

* **Table initialization logic**
  The ingestion script (`init/csv_ingestion.py`) automatically **creates** the `documents` table or **appends** data if it already exists.
  To **drop and rebuild** the table, run the script with the `--overwrite` flag (see `scripts/init_server.sh`).

---

### ☁️ AWS Usage

The server supports **Continuous Deployment (CD)**.
See the upcoming CD rule documentation [TBD].

---