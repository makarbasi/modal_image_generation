# Feature Report: FLUX.2 Image-to-Image Editing API
**Date**: May 23, 2026
**Component**: Smart Wish AI Laboratory

## Overview
We successfully implemented a new serverless Image-to-Image (img2img) processing pipeline utilizing the **black-forest-labs/FLUX.2-klein-4B** model. This allows users to supply a base image along with natural language editing instructions to generate a stylistically altered output image.

## Implementation Architecture
1. **Isolated Infrastructure**: To ensure resource and budget isolation, the feature was deployed on a completely separate Modal application (`smart-wish-image-edit`) using a distinct volume mount (`model-cache-img-edit`).
2. **Compute Tier**: The model is executed on an NVIDIA L4 GPU. We initialized `Flux2Pipeline` with `bfloat16` precision for optimal VRAM usage. 
3. **Gateway**: A dedicated HTTP POST endpoint (`/api/edit-image`) was configured on the local Express proxy, tunneling base64-encoded payloads to the Modal backend securely.

## Technical Nuances & Challenges
### The Mistral-v3 Tokenizer Bug
The most significant hurdle was an underlying bug discovered within the `diffusers` library. When attempting img2img inference with FLUX.2, the pipeline threw a `TypeError` deep inside the Jinja renderer (`TypeError: can only concatenate str to str`). 

**Root Cause**: The `format_input` function in `diffusers.pipelines.flux2.pipeline_flux2` was incorrectly pushing a list of characters instead of a properly formatted chat template array `[{"role": "user", "content": prompt}]`.

**Resolution**: Rather than waiting for an upstream patch, we engineered a runtime **Monkey-Patch** inside `image_edit.py`. This safely intercepts the `format_input` method right before GPU execution, forces it to return a single chat payload with string content, and perfectly satisfies the tokenizer's chat template.

## Cost & Efficiency
- **Execution Speed**: Inference takes roughly ~1.5 - 3.5 seconds per invocation due to our aggressive 8-step denoising schedule (`num_inference_steps=8`) and caching.
- **Cost**: Modal's L4 tier bills strictly by the millisecond during active processing. With aggressive 300-second scale-down windows, the cost overhead is extremely minimal (fraction of a cent per generation). The strict separation from the text-to-image server means we don't spin up heavy endpoints unless specifically testing the edit lab.

## Future Improvements
1. **In-painting capabilities**: Currently, the entire image is processed globally based on the edit `strength` slider. Implementing a masking UI layer would allow users to isolate edits to specific regions (e.g., "turn only the apple green").
2. **LoRA injection**: Adding support for dynamically passing LoRA adapters in the payload to allow specific stylistic edits (e.g., "watercolor style").
3. **Asynchronous processing**: If demand scales, moving the HTTP endpoints to an async task queue (via Redis or Modal queues) and returning polling IDs to the frontend will prevent gateway timeouts on slower connections.
