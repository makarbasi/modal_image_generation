Author: Enzo Hins

Date: April 21, 2026

---

Messy Statistics

|              Model              |  Task Category   | Quantization | TTFT (ms) | Peak VRAM |
| :-----------------------------: | :--------------: | :----------: | :-------: | :-------: |
|          Llama 4 (8B)           | Creative Writing |    Q8\_0     |   200ms   |  8.4 GB   |
|          Gemma 3 (7B)           | Creative Writing |    Q8\_0     |   200ms   |  7.6 GB   |
|      FLUX.1 \[dev\] (12B)       | Image Generation |     FP8      |   1.5s    |  13.8 GB  |
|      FLUX.2 \[dev\] (32B)       | Image Generation |     FP8      |   1.25s   |  14.2 GB  |
| FLUX.2 \[klein\] (**4B** or 9B) | Image Generation |     FP8      |   500ms   |  8.1 GB   |
|         RMBG-1.4 (176M)         |  Image editing   |     ONNX     |   50ms    |  0.8 GB   |

## Quantization methods

Q8\_0 (Llama 4 and Gemma 3\)

* It's almost lossless, cuts the model size in half (16-bit to 8-bit).  
* With my 16GB VRAM, I didn't need to use Q4, which would show in the results, text quality was still amazing.

FP8 (FLUX.1 and FLUX.2)

* A special 8-bit format that maintains the mathematical precision for complex images.  
* It’s the only way to fit 30GB models onto a 16GB card while keeping signatures and textures looking real.

ONNX (RMBG-1.4)

* A specialized high speed format that strips the model down to its bare math for maximum performance.  
* It makes background removal happen in milliseconds.  
  ---

  ## Implementation Details

  ### Hardware: AMD Ryzen 7 7800X3D | Radeon RX 7800 XT (16GB VRAM) | 32GB DDR5 RAM

* Ollama (LLM Engine):  
- **Deployment**: Installed the native Windows version of Ollama, utilizes the ROCm backend for AMD 7000-series cards.   
  - (Radeon Open Compute) is AMD's open-source software stack designed for GPU-accelerated computing. It is essentially AMD’s answer to NVIDIA’s CUDA.  
- **Usage**: Tested message generation efficiency (e.g., vet school graduation messages).  
* ComfyUI (Image Engine):  
- Deployment: Used the ComfyUI Windows build, used native AMD execution to minimize use of CPU. Ease of use was important to me for testing as I am new to locally running ai, it is a frontend like Ollama except for image generation.  
- Logic: Tested FLUX.2 \[klein\] for speed followed by FLUX.2 \[dev\] for high fidelity stress tests.  
* RMBG-1.4 (Post-FX):  
  * Deployment: Integrated via a Python script using onnxruntime-directml for background removal.  
  * Logic: Validated the transparent sticker conversion speed for the automated design suite. RMBG is trained on a data set where it knows what to isolate based on what the human eye would mainly be drawn to. Possibly would require another model if we would like the user to choose what to isolate.

  ---

  ## What and Why?

* Why FLUX.2 over FLUX.1?  
- FLUX.2 offers superior JSON-structured prompting and higher text legibility for specific brand signatures and details .  
- The Small Decoder in FLUX.2 gives much faster outputs.  
* Why not larger models?  
- The 8B/7B range provides the best throughput to VRAM ratio for 16GB cards.  
* What is the benefit of the 16GB VRAM on the 7800 XT?  
- It allows for 8-bit quantization (50% size reduction with only 1% error) rather than the more aggressive aggressive 4-bit, ensuring higher accuracy.  
  ---

  ## Example Prompts

* Message Gen:   
  * "System: Smart Wish Assistant. Task: Write a short graduation card message for a sister in vet school. Include one dog pun."  
* Visual Gen:   
  * "A minimalist greeting card on a desk, including a dog in a graduation cap and signature 'Warmest Regards' in realistic cursive."

  ---

  ## Outputs

Llama 4 (8B) / Gemma 3 (7B)

* What it spit out: Llama 4 gave me a super short but properly formatted message, while Gemma 3 was wordier and felt more like a real card.  
* The Vibe: Llama is a beast at following rules and staying in a specified format, so it’s good for agentic assisted back-end creation of messages.

FLUX.1 \[dev\]

* What it spit out: This made a clean-looking card and good texture.  
* The Vibe: It’s a good but costly baseline. It got the signature right, but it’s definitely slower than the version 2 models.

FLUX.2 \[dev\]

* What it spit out: This one made an impressive card and followed the prompt and brand style better. I saw this described in its comparison to flux 1 dev.  
* The Vibe: It’s way better at putting things exactly where I tell it to without making the image look weird.

FLUX.2 \[klein\]

* What it spit out: I got a decent preview of the card in like 4 seconds. It's not as high quality, but it's perfectly passable.  
* The Vibe: This model provides a “good enough” image.

RMBG-1.4

* What it spit out: I took a dog image I generated and it deleted the background instantly, keeping all lots of detail without making the edges look weird.   
* The Vibe: It runs crazy fast on the 7800 XT, so we can basically turn anything into a sticker without the user even noticing a loading bar.