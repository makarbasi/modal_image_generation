# Smart Wish AI: Intelligence Layer (`/services/ai_engine`)

This directory contains the production-grade inference engines for the Smart Wish ecosystem. It is designed to operate as a completely isolated layer handling high-performance AI inference on GPU hardware.

## 🧠 Core Services

### 1. Text Generation (`core/text_gen.py`)
*   **Engine**: Google Gemma-4B-it.
*   **Capabilities**: Single-message generation and structured variation generation (Professional, Casual, Loving).
*   **Reliability**: Implements LLM pre-filling and programmatic markdown stripping to ensure stable JSON delivery.

### 2. Visual Generation (`core/image_gen.py`)
*   **Engine**: Flux.2 [klein].
*   **Capabilities**: High-fidelity 1024x1024 PNG asset creation.
*   **Efficiency**: Uses `bfloat16` precision for optimal VRAM utilization on NVIDIA L4 GPUs.

### 3. Image Edit (img2img) (`core/image_edit.py`)
*   **Engine**: Flux.2 [klein].
*   **Capabilities**: Natural language instructional editing of base images.
*   **Efficiency**: Custom runtime diffusers patch to ensure stable integration; uses a separate Modal application volume to completely isolate inference limits from standard generation.

---

## 🛠 Deployment Workflow

### Step 1: Deploy to Modal
Ensure your `huggingface-secret` is active in your Modal workspace.
```bash
# Execute from the repository root
modal deploy services/ai_engine/core/text_gen.py
modal deploy services/ai_engine/core/image_gen.py
modal deploy services/ai_engine/core/image_edit.py
```

### Step 2: Integration with the Web Orchestrator
The `services/web_server/api` server acts as a managed proxy for these services. To connect them:
1.  Locate the generated FastAPI URLs in your Modal dashboard.
2.  Update `services/web_server/.env` with these values:
    ```env
    GEMMA_MODAL_URL=https://<endpoint>.modal.run
    FLUX_MODAL_URL=https://<endpoint>.modal.run
    FLUX_EDIT_MODAL_URL=https://<endpoint>.modal.run
    ```

---

## 👨‍💻 Engineering Patterns
The services in this directory follow the **Inference Worker Pattern**. They are designed to be stateless, serverless, and highly available. By exposing FastAPI endpoints, they allow the `services/web_server` layer (Node.js) to perform orchestration without needing to manage complex GPU dependencies or model weight loading.
