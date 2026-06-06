# Engineering Report: User Input Sanitization MVP

**Date:** May 28, 2026  
**Subject:** Implementation, Validation, and Strategic Assessment of Prompt Sanitization Pipeline  

---

## Implementation Overview

The prompt sanitization feature was introduced to address the inherent unpredictability of raw user inputs, which frequently suffer from grammatical errors, conversational clutter (e.g., "Hey AI, please draw..."), extreme brevity, and potential injection vectors. To maximize the quality of downstream generative models, we implemented a **Sequential LLM Sanitization Pipeline** as our Phase 1 MVP.

### System Architecture
The current architecture routes all incoming requests through an orchestration gateway before they reach the primary generation models. The workflow is structured as follows:

1. **Frontend Interception**: The user submits a raw prompt via the UI.
2. **Orchestration Gateway**: The Express.js server intercepts the request and blocks downstream generation.
3. **Stage 1 (Sanitization)**: The gateway makes an RPC/HTTP call to a dedicated `sanitize_input` method running on a Modal GPU worker (powered by Gemma-4B). This step runs with deterministic parameters (`temperature=0.3`, `max_new_tokens=200`) to guarantee high-fidelity rewrites.
4. **Stage 2 (Generation)**: The newly sanitized, descriptive prompt is returned to the gateway, which then forwards it to the appropriate downstream endpoint (`generate_variations` via Gemma-4B or image generation via Flux).
5. **UI Delivery**: The gateway returns the final payload along with the intermediate `sanitized_prompt` to visualize the pipeline's impact.

### Edge Case Handling
The Gemma-4B sanitization prompt was explicitly engineered to handle the following edge cases:
* **Conversational Filler Removal**: Successfully scrubs redundant preambles ("Can you write me a card...").
* **Typo and Grammar Correction**: Reconstructs misspelled or structurally poor sentences into proper grammatical formats.
* **Sparse Input Expansion**: Enriches extremely brief inputs (e.g., "a dog") into highly descriptive, detailed prompts tailored for text or image modalities.

---

## E2E Testing & Performance Validation

To validate the MVP, we executed comprehensive End-to-End (E2E) integration tests across all three primary generative pipelines (Text-to-Text, Text-to-Image, and Image-to-Image). The testing suite confirms that the sanitization logic successfully transforms inputs, though it introduces measurable latency overhead.

### Validation Results & Telemetry

* **Text-to-Text Pipeline (Greeting Card Variations)**
  * *Raw Input:* `"Hey AI can u write me a bday card for my coder friend sarah who loves warm coffee"`
  * *Sanitized Output:* `"A warm and cheerful birthday card message for a coder friend named Sarah who loves warm coffee."`
  * **Sanitization Latency:** **1,867 ms**
  * **Generation Latency:** **8,829 ms**
  * **Total Pipeline Latency:** **10,696 ms**

* **Text-to-Image Pipeline (Flux Generation)**
  * *Raw Input:* `"Draw me a picture of a cute kitten sitting in a tea cup"`
  * *Sanitized Output:* `"An adorable, fluffy kitten nestled cozily inside a delicate, antique porcelain teacup, soft morning sunlight streaming in from a nearby window, shallow depth of field...`
  * **Sanitization Latency:** **3,864 ms**
  * **Generation Latency:** **13,763 ms**
  * **Total Pipeline Latency:** **17,627 ms**

* **Image-to-Image Pipeline (Flux Edit)**
  * *Raw Input:* `"Make the kitten wear a tiny blue wizard hat and add soft sparkles"`
  * *Sanitized Output:* `"A photorealistic portrait of an adorable kitten wearing a miniature, intricately detailed sapphire blue wizard hat, illuminated by soft, ethereal bokeh lights..."`
  * **Sanitization Latency:** **4,138 ms**
  * **Generation Latency:** **75,287 ms**
  * **Total Pipeline Latency:** **79,425 ms**

### Performance Assessment
The E2E tests validate the functional correctness of the prompt enrichment. However, the telemetry reveals a core drawback of the sequential architecture: **Sanitization adds between ~1.8s and ~4.1s of latency per transaction.** Because we are executing two sequential round-trips to Modal GPU-accelerated endpoints, we effectively double the cold-start risk and noticeably degrade the user experience for faster text-based tasks.

---

## Strategic Alternatives & Improvements

While the Phase 1 MVP establishes a functional baseline, the current architecture is economically inefficient and latency-heavy. The GPU compute cost on Modal scales linearly with active container time, effectively doubling our infrastructure costs per request. 

To resolve these architectural bottlenecks, I propose the following concrete improvements for Phase 2:

### 1. API Gateway-Level Sanitization (Highly Recommended)
* **Architecture**: Deprecate the Modal-hosted Gemma-4B sanitization worker. Instead, integrate a fast, serverless API call (e.g., Gemini 1.5 Flash or Claude 3 Haiku) directly into the Node.js Express orchestration layer.
* **Trade-offs**: 
  * *Pros:* Reduces sanitization latency from seconds to milliseconds (**< 500ms** expected). Completely eliminates Modal GPU runtime costs for Stage 1. Hosted models offer superior instruction-following without container boot overhead.
  * *Cons:* Introduces a third-party API dependency and requires managing external API keys.

### 2. UI-Driven Deterministic Structuring
* **Architecture**: Refactor the frontend UI to replace open-ended text fields with structured, enforced input parameters (e.g., dropdowns for recipient, toggle buttons for tone, specific input fields for occasion). 
* **Trade-offs**: 
  * *Pros:* Replaces unpredictable NLP preprocessing with deterministic string concatenation at the gateway level. Yields **0 ms latency overhead** and guarantees **100% format reliability**.
  * *Cons:* Reduces the "magic" of a natural language conversational interface, potentially limiting user expression.

### 3. Asynchronous / Speculative Execution
* **Architecture**: Run a fast, unsanitized "draft" generation in parallel with the sanitization pipeline. If the raw prompt is deemed "good enough" by a lightweight classifier, we return the draft immediately. If it requires sanitization, we wait for the sanitized pipeline to complete.
* **Trade-offs**: 
  * *Pros:* Optimizes perceived latency for well-formatted prompts.
  * *Cons:* Significantly increases architectural complexity and risks wasting compute on discarded draft generations.

### Recommendation
Moving forward, implementing **Alternative 1 (API Gateway-Level Sanitization)** provides the highest immediate ROI by drastically reducing both latency and GPU costs while preserving the natural language user experience.
