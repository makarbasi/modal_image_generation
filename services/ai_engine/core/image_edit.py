"""
Smart Wish AI - Image Edit Service (img2img)

Deploys Flux.2 [klein] as an image-to-image editor on Modal.
This is a SEPARATE deployment from the text-to-image service
(smart-wish-image) for full isolation.

Usage:
    modal deploy ai/src/image_edit.py
"""

import modal
import io

# ──────────────────────────────────────────────
# 1. Modal App + Container Image
# ──────────────────────────────────────────────

app = modal.App("smart-wish-image-edit")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")
    .pip_install(
        "transformers",
        "torch",
        "torchvision",
        "accelerate",
        "git+https://github.com/huggingface/diffusers.git",
        "huggingface_hub",
        "peft",
        "hf_transfer",
        "sentencepiece",
        "fastapi[standard]",
        "Pillow",
    )
    .env({
        "HF_HUB_ENABLE_HF_TRANSFER": "1",
        "HF_HOME": "/cache",
        "CACHE_BUSTER": "6",
    })
)

MODEL_ID = "black-forest-labs/FLUX.2-klein-4B"

# Separate volume — no sharing with the txt2img service.
model_cache = modal.Volume.from_name("model-cache-img-edit", create_if_missing=True)


# ──────────────────────────────────────────────
# 2. Service Class
# ──────────────────────────────────────────────

@app.cls(
    image=image,
    gpu="L4",
    secrets=[modal.Secret.from_name("huggingface-secret")],
    scaledown_window=300,
    volumes={"/cache": model_cache},
    startup_timeout=3600,
    timeout=3600,
)
class ImageEditService:
    """Serverless img2img worker.
    
    Accepts a source image and a text instruction, and returns the edited image.
    This service runs on an isolated Modal volume to prevent rate limits from 
    impacting the standard text-to-image generator.
    """

    @modal.enter()
    def load_model(self):
        """Initializes the Flux 2 Klein pipeline into VRAM.
        
        Executed exactly once per container lifecycle. It also applies a runtime 
        monkey patch to the diffusers library to bypass a known tokenization bug 
        with the Mistral tokenizer when handling image inputs.
        """
        from diffusers import Flux2Pipeline
        import torch

        print("🖌️  Booting Flux.2 [klein] Image Edit Engine...")
        self.pipe = Flux2Pipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.bfloat16,
        ).to("cuda")
        print("✅ Image Edit Engine Ready.")

        # Monkey-patch diffusers format_input to bypass a bug in Mistral tokenizer handling
        import diffusers.pipelines.flux2.pipeline_flux2 as p
        if getattr(p, "format_input", None):
            def patched_format_input(prompts, system_message=""):
                prompt_str = prompts[0] if isinstance(prompts, list) else prompts
                cleaned = prompt_str.replace("[IMG]", "")
                return [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": cleaned}
                ]
            p.format_input = patched_format_input

    def _edit_image(
        self,
        image_bytes: bytes,
        prompt: str,
        strength: float = 0.75,
        steps: int = 8,
        guidance: float = 3.5,
    ) -> bytes:
        """Executes the core image-to-image inference loop.
        
        Resizes the incoming image to 1024x1024 (the optimal resolution for Flux.2)
        and applies the edit instruction using the specified denoising strength.
        
        Args:
            image_bytes (bytes): Raw PNG/JPEG bytes of the source image.
            prompt (str): Natural-language edit instruction.
            strength (float, optional): How much to deviate from the source 
                                        (0.0 = no change, 1.0 = full regen). Defaults to 0.75.
            steps (int, optional): Number of denoising steps. Defaults to 8.
            guidance (float, optional): Classifier-free guidance scale. Defaults to 3.5.

        Returns:
            bytes: A byte stream representing the edited PNG image.
        """
        from PIL import Image
        import torch

        # Decode the incoming image and resize to 1024x1024 for the model.
        source = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        source = source.resize((1024, 1024), Image.LANCZOS)

        with torch.no_grad():
            result = self.pipe(
                prompt=prompt,
                image=source,
                num_inference_steps=steps,
                guidance_scale=guidance,
                height=1024,
                width=1024,
            ).images[0]

        buf = io.BytesIO()
        result.save(buf, format="PNG")
        return buf.getvalue()

    # ── RPC endpoint (for CLI / cross-service calls) ──

    @modal.method()
    def edit_image(
        self,
        image_bytes: bytes,
        prompt: str,
        strength: float = 0.75,
        steps: int = 8,
        guidance: float = 3.5,
    ) -> bytes:
        """Exposed RPC method for cross-service image editing.
        
        This serves as the secure, remote entry point for generating images 
        via CLI scripts or direct backend-to-backend communication.
        
        Args:
            image_bytes (bytes): Raw PNG/JPEG bytes of the source image.
            prompt (str): Natural-language edit instruction.
            strength (float, optional): Deviation strength. Defaults to 0.75.
            steps (int, optional): Denoising steps. Defaults to 8.
            guidance (float, optional): Guidance scale. Defaults to 3.5.
            
        Returns:
            bytes: A byte stream representing the edited PNG image.
        """
        return self._edit_image(image_bytes, prompt, strength, steps, guidance)

    # ── HTTP endpoint (for web integration) ──

    @modal.fastapi_endpoint(method="POST")
    def web_edit_v4(self, request: dict):
        """Public FastAPI gateway for web integration.
        
        This endpoint allows the Node.js orchestrator to request image edits 
        via standard HTTP POST. It decodes the incoming base64 image, processes 
        the edit, and returns a new base64 encoded data URI for the frontend.

        Args:
            request (dict): The parsed JSON payload containing 'image_base64', 
                            'prompt', and optionally 'strength' and 'steps'.

        Returns:
            dict: A dictionary containing the 'image_url' (data URI) or an HTTP 400 error.
        """
        import base64

        image_b64 = request.get("image_base64")
        prompt = request.get("prompt")
        strength = float(request.get("strength", 0.75))
        steps = int(request.get("steps", 8))

        if not image_b64 or not prompt:
            return {"error": "Both 'image_base64' and 'prompt' are required."}, 400

        image_bytes = base64.b64decode(image_b64)
        edited_bytes = self._edit_image(image_bytes, prompt, strength, steps)
        edited_b64 = base64.b64encode(edited_bytes).decode("utf-8")

        return {"image_url": f"data:image/png;base64,{edited_b64}"}
