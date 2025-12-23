# Zaban Frontend

This is the Next.js frontend dashboard for the Zaban platform. It allows users to manage their profiles, view usage analytics, and generate API keys.

## Integration

This frontend communicates with the **Zaban Backend** (FastAPI). Ensure the backend is running for full functionality.

## Prerequisites

*   Node.js 18+
*   npm (or yarn/pnpm/bun)

## Getting Started

### 1. Installation

Navigate to the frontend directory and install dependencies:

```bash
cd frontend
npm install
```

### 2. Environment Configuration

Create a `.env` file in the `frontend` directory by copying the example:

```bash
cp .env.example .env
```

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser.

## Docker

To build and run the frontend using Docker standalone:

```bash
# Build
docker build -t zaban-frontend .

# Run
docker run -p 3000:3000 --env-file .env zaban-frontend
```

*Note: It is recommended to use the root `docker-compose.yml` to run both frontend and backend together.*

## Project Structure

*   `app/`: Main application code (App Router).
*   `public/`: Static assets.
*   `lib/`: Utility functions and API service clients.
