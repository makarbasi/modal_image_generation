/**
 * Smart Wish AI - Orchestration Layer (Node.js/Express)
 * 
 * This server acts as a managed proxy between the client-side UI and the 
 * Modal-hosted AI microservices. It centralizes environment configuration,
 * handles CORS/security concerns, and simplifies the API surface for the frontend.
 * 
 * Architecture Note:
 * This layer is deliberately decoupled from the inference workers to allow 
 * independent scaling and to prevent the frontend from directly exposing 
 * sensitive API keys or complex Model orchestration logic.
 * 
 * @module server
 */

const express = require('express');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware configuration
app.use(express.json({ limit: '20mb' }));
app.use(express.static(path.join(__dirname, '../client')));

// Service Discovery: Internal URLs for Modal workers.
const GEMMA_URL = process.env.GEMMA_MODAL_URL;
const FLUX_URL = process.env.FLUX_MODAL_URL;
const FLUX_EDIT_URL = process.env.FLUX_EDIT_MODAL_URL;

/**
 * Helper to sanitize prompts via the Gemma worker.
 * @param {string} prompt - The raw user prompt.
 * @param {boolean} isImage - Whether the prompt is for image generation.
 * @returns {Promise<{sanitizedPrompt: string, sanitizationMs: number}>}
 */
async function sanitizeUserPrompt(prompt, isImage = false) {
    const start = Date.now();
    let sanitizedPrompt = prompt;

    try {
        const payload = isImage ? { prompt, sanitize_image: true } : { prompt, sanitize: true };
        const res = await fetch(GEMMA_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (data.sanitized_prompt) {
            sanitizedPrompt = data.sanitized_prompt;
        }
    } catch (err) {
        const type = isImage ? 'Image Sanitization' : 'Text Sanitization';
        console.warn(`[${type}] Fallback to raw prompt:`, err.message);
    }

    return { sanitizedPrompt, sanitizationMs: Date.now() - start };
}

/**
 * Text Generation Proxy Endpoint
 * 
 * Routes incoming text generation requests from the client to the remote 
 * Gemma-4B worker on Modal. Handles both single message generation and 
 * structured JSON variation requests.
 * 
 * @name POST /api/generate-text
 * @function
 * @param {express.Request} req - The Express request object containing the user's prompt, optional context, and boolean flag for variations.
 * @param {express.Response} res - The Express response object used to send back the generated text or JSON structure.
 */
app.post('/api/generate-text', async (req, res) => {
    try {
        const { prompt, context, variations } = req.body;
        
        if (variations) {
            const { sanitizedPrompt, sanitizationMs } = await sanitizeUserPrompt(prompt, false);

            const genStart = Date.now();
            const response = await fetch(GEMMA_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: sanitizedPrompt, variations: true })
            });

            const data = await response.json();
            const generationMs = Date.now() - genStart;
            
            return res.json({
                ...data,
                sanitized_prompt: sanitizedPrompt,
                timings: { sanitization_ms: sanitizationMs, generation_ms: generationMs, total_ms: sanitizationMs + generationMs },
            });
        }
        
        const response = await fetch(GEMMA_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, context, variations })
        });

        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('[Orchestration Error] Gemma Proxy failed:', error);
        res.status(500).json({ error: 'Service Unavailable' });
    }
});

/**
 * Image Generation Proxy Endpoint
 * 
 * Routes visual prompts from the client to the remote Flux image generation worker.
 * Implicitly runs prompt sanitization prior to generation.
 * 
 * @name POST /api/generate-image
 * @function
 * @param {express.Request} req - The Express request object containing the raw image prompt.
 * @param {express.Response} res - The Express response object used to send back the generated base64 image data URI.
 */
app.post('/api/generate-image', async (req, res) => {
    try {
        const { prompt } = req.body;

        const { sanitizedPrompt, sanitizationMs } = await sanitizeUserPrompt(prompt, true);

        const genStart = Date.now();
        const response = await fetch(FLUX_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: sanitizedPrompt })
        });

        const data = await response.json();
        const generationMs = Date.now() - genStart;

        res.json({
            ...data,
            sanitized_prompt: sanitizedPrompt,
            timings: { sanitization_ms: sanitizationMs, generation_ms: generationMs, total_ms: sanitizationMs + generationMs }
        });
    } catch (error) {
        console.error('[Orchestration Error] Flux Proxy failed:', error);
        res.status(500).json({ error: 'Service Unavailable' });
    }
});

/**
 * Image Edit Proxy Endpoint
 * 
 * Routes image-to-image modification requests to the dedicated Flux edit worker.
 * This ensures that heavy img2img processing is isolated from standard generation.
 * 
 * @name POST /api/edit-image
 * @function
 * @param {express.Request} req - The Express request object containing the base64 source image, textual prompt, and optional strength/steps.
 * @param {express.Response} res - The Express response object used to send back the modified base64 image data URI.
 */
app.post('/api/edit-image', async (req, res) => {
    try {
        const { image_base64, prompt, strength, steps } = req.body;

        const { sanitizedPrompt, sanitizationMs } = await sanitizeUserPrompt(prompt, true);

        const genStart = Date.now();
        const response = await fetch(FLUX_EDIT_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image_base64, prompt: sanitizedPrompt, strength, steps })
        });

        const data = await response.json();
        const generationMs = Date.now() - genStart;

        res.json({
            ...data,
            sanitized_prompt: sanitizedPrompt,
            timings: { sanitization_ms: sanitizationMs, generation_ms: generationMs, total_ms: sanitizationMs + generationMs }
        });
    } catch (error) {
        console.error('[Orchestration Error] Flux Edit Proxy failed:', error);
        res.status(500).json({ error: 'Service Unavailable' });
    }
});

// Bootstrapping
if (require.main === module) {
    app.listen(PORT, () => {
        console.log(`
🚀 Smart Wish Orchestrator Active
---------------------------------
Local Gateway: http://localhost:${PORT}
Text Worker:  ${GEMMA_URL ? 'Connected' : 'DISCONNECTED'}
Image Worker: ${FLUX_URL ? 'Connected' : 'DISCONNECTED'}
Edit Worker:  ${FLUX_EDIT_URL ? 'Connected' : 'DISCONNECTED'}
        `);
    });
}

module.exports = app;
