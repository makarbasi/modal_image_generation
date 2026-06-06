# Smart Wish AI: Generative Studio Ecosystem

A professional-grade, full-stack generative AI platform for personalized greeting card creation. This ecosystem leverages high-performance serverless inference, a managed orchestration layer, and a modern web interface.

---

## 🏗 System Architecture

The repository is organized into a domain-driven file hierarchy for maximum decoupling, readability, and ease of integration:

### 1. Intelligence Layer (`/services/ai_engine`)
Serverless Python microservices deployed on **Modal**.
*   **Text Engine**: Powered by Google's `Gemma-4B-it`. Features advanced prompt engineering for structured (JSON) multi-tone output.
*   **Visual Engine**: Powered by Black Forest Labs' `Flux.2-klein-4B`. Optimized for high-fidelity 1024x1024 asset generation.
*   **Image Edit Engine (img2img)**: Also powered by `Flux.2-klein-4B`, deployed on isolated GPU infrastructure to allow users to apply instructional edits to existing images.
*   **Safeguards**: Built-in programmatic markdown stripping and JSON structural validation.

### 2. Orchestration Layer (`/services/web_server/api`)
A managed Node.js/Express gateway.
*   **Security & Proxy**: Centralizes environment management and proxies client requests to serverless workers.
*   **Service Discovery**: Maps local API routes to remote Modal endpoints via `.env`.

### 3. Presentation Layer (`/services/web_server/client`)
A premium, responsive web interface.
*   **Rich Aesthetics**: Utilizes glassmorphism, dynamic gradients, and micro-animations for a high-end user experience.
*   **Real-time Interaction**: Integrated Text and Image Laboratories with live generation status.

---

## 🚀 Deployment & Setup

### AI Microservices (Modal)
Ensure you have a Modal account and `huggingface-secret` configured.
```bash
# From root
modal deploy services/ai_engine/core/text_gen.py
modal deploy services/ai_engine/core/image_gen.py
modal deploy services/ai_engine/core/image_edit.py
```

### Web Gateway
1.  Configure `services/web_server/.env` with the URLs provided by the Modal deployment.
2.  Install dependencies and boot the orchestrator:
    ```bash
    cd services/web_server
    npm install
    node api/server.js
    ```

---

## 📁 Repository Navigation

*   `services/ai_engine/`: Production-ready service definitions and inference engines.
*   `services/web_server/`: Full-stack web application and orchestration server.
*   `docs/`: Technical documentation, architectural reviews, and project status reports.
*   `archive/`: Legacy scripts and historical files preserved for reference.

---

## 👨‍💻 Integration Note for Senior Engineers
This ecosystem is built as a reference for decoupled AI integration. The separation between the **Inference Layer** (Python/FastAPI on GPU) and the **Orchestration Layer** (Node.js/Express) allows for maximum flexibility in production environments where different teams may manage the AI models and the product backend.
