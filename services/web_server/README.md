# Smart Wish AI: Orchestration Layer (`/services/web_server`)

This directory contains the Node.js/Express gateway and the web frontend client for the Smart Wish ecosystem.

## ⚙️ Purpose

The Orchestration Layer acts as a managed proxy between the presentation client and the intelligence microservices.
- **Security & Proxying**: It centralizes environment variables and abstracts the remote AI endpoint URLs away from the client.
- **CORS Management**: It handles Cross-Origin requests natively.
- **Static Hosting**: It serves the `client/` directory containing the frontend UI.

## 🚀 Setup & Execution

### Dependencies
Ensure you have Node.js installed (v18+ recommended).

1.  Navigate to the web server directory:
    ```bash
    cd services/web_server
    ```
2.  Install required NPM packages:
    ```bash
    npm install
    ```
3.  Create a `.env` file in this directory and populate it with the Modal AI endpoints:
    ```env
    PORT=3000
    GEMMA_MODAL_URL=https://<your-gemma-endpoint>.modal.run
    FLUX_MODAL_URL=https://<your-flux-endpoint>.modal.run
    FLUX_EDIT_MODAL_URL=https://<your-flux-edit-endpoint>.modal.run
    ```

### Running the Server

Start the orchestration server locally:
```bash
node api/server.js
```
The application will be accessible at `http://localhost:3000`.

## 📂 Architecture

-   `api/server.js`: The Express proxy server. Handles incoming client requests, attaches necessary headers, and forwards payloads to the AI layer.
-   `client/`: The Presentation Layer. Contains vanilla HTML/CSS/JS for the responsive user interface.
    -   `app.js`: Client-side logic for DOM manipulation and asynchronous API calls to the local proxy.
    -   `index.html`: Main entry point for the UI.
    -   `style.css`: Design tokens and responsive layouts.
