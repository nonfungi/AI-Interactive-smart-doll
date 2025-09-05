# AI Interactive Smart Doll - Backend API

Welcome to the backend repository for the **AI Interactive Smart Doll**, a sophisticated conversational AI designed to be an engaging and educational companion. This project currently functions as a **web-first API**, allowing interaction via voice through a web client, with future plans for integration into a physical hardware device.

## 🌟 Project Overview

This project provides the core services for a smart, interactive AI. It's built with a modern, scalable tech stack to handle real-time voice conversations, manage user data securely, and provide a persistent, personalized memory for each user.

## 🧠 Core Features

-   **End-to-End Voice Interaction:** A complete pipeline that transcribes user audio (**OpenAI Whisper**), generates a contextual response using a RAG pipeline, and converts it back to speech (**Hugging Face TTS**).
-   **RAG-based Conversational AI:** Utilizes a Retrieval-Augmented Generation (RAG) pipeline with **LangChain** to provide context-aware and non-repetitive answers.
-   **Personalized Long-Term Memory:** Each child has a dedicated collection in a **Qdrant** vector database, allowing the AI to remember past conversations.
-   **Multi-User Architecture:** A robust user management system built with **PostgreSQL** and **SQLAlchemy**, supporting parents, children, and doll profiles with secure **JWT authentication**.
-   **Containerized & Scalable:** The entire application is containerized using **Docker** and orchestrated with **Docker Compose** for easy, reproducible local setup and future deployment.

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| **Backend** | Python, FastAPI, Uvicorn |
| **AI & ML** | LangChain, Qdrant, OpenAI API, Hugging Face API |
| **Databases** | PostgreSQL (Relational), Qdrant (Vector) |
| **Authentication** | JWT (JSON Web Tokens), Passlib (Hashing) |
| **DevOps** | Docker, Docker Compose |
| **Testing** | Pytest |

## 🚀 How to Run Locally

This project is fully containerized, making the local setup incredibly simple.

### Prerequisites

-   Docker
-   Docker Compose

### Instructions

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/nonfungi/AI-Interactive-smart-doll.git](https://github.com/nonfungi/AI-Interactive-smart-doll.git)
    cd AI-Interactive-smart-doll
    ```

2.  **Create your environment file:**
    Copy the example environment file and fill in your secret keys.
    ```bash
    cp .env.example .env
    ```
    Now, open the `.env` file and add your `OPENAI_API_KEY`, `HUGGINGFACE_API_KEY`, and other secrets.

3.  **Run the application with Docker Compose:**
    This single command will build the images, start all containers (app, PostgreSQL, Qdrant), and set up the necessary networks and volumes.
    ```bash
    docker-compose up --build
    ```

4.  **Access the API:**
    The API will be running and available at `http://localhost:8001`. You can access the auto-generated documentation at `http://localhost:8001/docs`.

5.  **(Optional) Initialize Database Tables:**
    If you need to create the database tables manually, you can run the `create_tables.py` script. Make sure the database container is running first.

    *Note: The `docker-compose.yml` is configured to map the PostgreSQL port `5432` inside the container to `5433` on your host machine. The script `create_tables.py` is already configured for this.*