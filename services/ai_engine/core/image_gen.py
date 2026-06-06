"""
Smart Wish AI - Image Generation Service (Production Grade)

This module implements a serverless visual generation worker using Modal. It leverages
the Flux.2 [klein] model to produce high-fidelity 1024x1024 assets for greeting cards.

Architectural Design:
1.  **VRAM Optimization**: Uses bfloat16 precision to fit the 4B parameter model 
    comfortably within the 24GB VRAM limit of NVIDIA L4 GPUs.
2.  **Latency Reduction**: Utilizes persistent volumes for weight caching and 
    optimized diffusers pipelines for rapid 8-step denoising.
3.  **Scalable API**: Provides both high-performance RPC (remote methods) and 
    web-standard HTTP endpoints.
"""

import modal
import io

# Define the Modal application and compute cluster.
app = modal.App("smart-wish-image")

# Container image definition with specialized CUDA-enabled dependencies.
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
        "fastapi[standard]"
    )
    .env({
        "HF_HUB_ENABLE_HF_TRANSFER": "1",
        "HF_HOME": "/cache"
    })
)

MODEL_ID = "black-forest-labs/FLUX.2-klein-4B"

# Volume used to cache large model weights (~10GB) to prevent recurring download latencies.
model_cache = modal.Volume.from_name("model-cache-v2", create_if_missing=True)

@app.cls(
    image=image,
    gpu="L4",
    secrets=[modal.Secret.from_name("huggingface-secret")],
    scaledown_window=300,
    volumes={"/cache": model_cache},
    startup_timeout=3600,
    timeout=3600,
)
class ImageService:
    """
    Worker class for generative visual inference.
    """

    @modal.enter()
    def load_model(self):
        """Initializes the Flux pipeline in GPU memory.
        
        This method is executed exactly once per container lifecycle. It loads 
        the Flux.2 klein model weights with bfloat16 precision to fit comfortably 
        within the 24GB VRAM limit of an NVIDIA L4 GPU.
        """
        from diffusers import Flux2KleinPipeline
        import torch

        print(f"🎨 Booting Flux.2 [klein] Engine...")
        self.pipe = Flux2KleinPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.bfloat16
        ).to("cuda")
        print("✅ Image Engine Ready.")

    def _generate_image(self, prompt: str, steps: int = 8, guidance: float = 3.5) -> bytes:
        """Core inference implementation for image generation.
        
        Generates a 1024x1024 image using optimized denoising schedules. The inference 
        is executed within a no-grad context to maximize memory throughput.
        
        Args:
            prompt (str): The visual description for the image.
            steps (int, optional): Number of denoising steps. Defaults to 8.
            guidance (float, optional): Classifier-free guidance scale. Defaults to 3.5.
            
        Returns:
            bytes: A byte stream representing the generated PNG image.
        """
        import torch

        # Inference executed in a no-grad context to maximize throughput.
        with torch.no_grad():
            generated_image = self.pipe(
                prompt=prompt,
                num_inference_steps=steps,
                guidance_scale=guidance,
                height=1024,
                width=1024,
            ).images[0]

        # Serialize PIL object to PNG byte stream.
        buf = io.BytesIO()
        generated_image.save(buf, format="PNG")
        return buf.getvalue()

    @modal.method()
    def generate_image(self, prompt: str, steps: int = 8, guidance: float = 3.5) -> bytes:
        """Exposed RPC method for cross-service image generation.
        
        This serves as the secure, remote entry point for generating images 
        via CLI scripts or direct backend-to-backend communication.
        
        Args:
            prompt (str): The visual description.
            steps (int, optional): Number of denoising steps. Defaults to 8.
            guidance (float, optional): Guidance scale. Defaults to 3.5.
            
        Returns:
            bytes: A byte stream representing the generated PNG image.
        """
        return self._generate_image(prompt, steps, guidance)

    @modal.fastapi_endpoint(method="POST")
    def web_generate(self, request: dict):
        """Public FastAPI gateway for web integration.
        
        This endpoint allows the Node.js orchestrator to request image generation 
        via standard HTTP POST. It converts the generated image bytes into a 
        base64 encoded data URI for immediate rendering on the frontend client.
        
        Args:
            request (dict): The parsed JSON payload containing the 'prompt'.
            
        Returns:
            dict: A dictionary containing the 'image_url' (data URI) or an HTTP 400 error.
        """
        import base64
        prompt = request.get("prompt")

        if not prompt:
            return {"error": "Prompt parameter is required."}, 400

        image_bytes = self._generate_image(prompt)
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        return {"image_url": f"data:image/png;base64,{base64_image}"}
