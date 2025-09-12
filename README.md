title: AI Interactive Smart Doll sdk: docker app_port: 8001
AI Interactive Smart Doll - Backend API
Welcome to the backend repository for the AI Interactive Smart Doll, a sophisticated conversational AI designed to be an engaging and educational companion for children.

🚀 Live Demo
You can test the live version of the AI Smart Doll right now by visiting our Hugging Face Space! The interactive UI is served directly from the backend.

🌟 Project Overview
This project provides the core services for a smart, interactive AI. It's built with a modern, scalable tech stack to handle real-time voice conversations, manage user data securely, and provide a persistent, personalized memory for each user.

🧠 Core Features
End-to-End Voice Interaction: A complete pipeline that transcribes user audio (OpenAI Whisper), generates a contextual response (Google Gemini), and converts it back to high-quality speech (OpenAI TTS).

RAG-based Conversational AI: Utilizes a Retrieval-Augmented Generation (RAG) pipeline to provide context-aware and non-repetitive answers by searching through past conversations.

Personalized Long-Term Memory: Each child has a dedicated memory space in a Qdrant vector database, allowing the AI to remember and recall past interactions.

Multi-User Architecture: A robust user management system built with a cloud-native PostgreSQL database and SQLAlchemy, supporting secure JWT authentication.

Containerized & Cloud-Ready: The entire application is containerized using Docker for easy, reproducible local setup and is deployed on Hugging Face Spaces.

🛠️ Tech Stack
Category

Technology

Backend

Python, FastAPI, Uvicorn

AI & ML

Google Gemini, OpenAI (Whisper, TTS, Embeddings)

Databases

Neon Cloud (PostgreSQL), Qdrant Cloud (Vector)

Authentication

JWT (JSON Web Tokens), Passlib (Hashing)

DevOps & Hosting

Docker, Hugging Face Spaces

🚀 How to Run Locally
This project is fully containerized, making the local setup incredibly simple.

Prerequisites
Docker

Docker Compose

Instructions
Clone the repository:

git clone [https://github.com/nonfungi/AI-Interactive-smart-doll.git](https://github.com/nonfungi/AI-Interactive-smart-doll.git)
cd AI-Interactive-smart-doll

Create your environment file:
Copy the example environment file and fill in your secret keys for OpenAI, Neon, and Qdrant.

cp .env.example .env

Run the application with Docker Compose:
This command builds the images and starts the application container.

docker-compose up --build

Interact with the Doll:
Once the application is running, open your browser and go to http://localhost:8001. You will see the interactive web demo.

Access the API Documentation:
The auto-generated API documentation is available at http://localhost:8001/docs.