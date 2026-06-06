/**
 * Smart Wish AI - Frontend Application Logic
 * 
 * This module handles all client-side interactions for the Text Lab and Image Lab 
 * interfaces. It is responsible for gathering user inputs, managing the loading 
 * state of the DOM, performing asynchronous API calls to the Express orchestration 
 * proxy, and rendering the returned payloads (text, JSON, or base64 images).
 * 
 * @module clientApp
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // --- UI Element Selectors ---
    
    // Text Lab elements
    const genTextBtn = document.getElementById('gen-text-btn');
    const textPrompt = document.getElementById('text-prompt');
    const textContext = document.getElementById('text-context');
    const textResultContainer = document.getElementById('text-result-container');
    const textOutput = document.getElementById('text-output');
    const copyBtn = document.getElementById('copy-btn');
    const variationsToggle = document.getElementById('variations-toggle');
    const singleOutputContainer = document.getElementById('single-output-container');
    const variationsOutputContainer = document.getElementById('variations-output-container');
    const rawOutput = document.getElementById('raw-output');

    // Image Lab elements
    const genImageBtn = document.getElementById('gen-image-btn');
    const imagePrompt = document.getElementById('image-prompt');
    const imageResultContainer = document.getElementById('image-result-container');
    const imageOutput = document.getElementById('image-output');

    // --- Text Generation Logic ---

    /**
     * Text Generation Event Handler
     * 
     * Orchestrates the process of sending a text generation request. It reads 
     * the prompt and context fields, toggles the appropriate UI loading states, 
     * dispatches the fetch request to the backend proxy, and parses the response. 
     * If the variations toggle is active, it handles rendering the raw JSON payload.
     * 
     * @async
     * @listens click
     * @fires fetch
     */
    genTextBtn.addEventListener('click', async () => {
        const prompt = textPrompt.value.trim();
        const context = textContext.value.trim();
        const variations = variationsToggle.checked;

        if (!prompt) {
            alert('Please enter a message prompt!');
            return;
        }

        // Set UI to loading state
        setLoading(genTextBtn, true);
        textResultContainer.classList.remove('hidden');
        
        if (variations) {
            singleOutputContainer.classList.add('hidden');
            variationsOutputContainer.classList.remove('hidden');
            rawOutput.innerHTML = '<span class="loading-dots"></span>';
            document.getElementById('sanitization-panel').classList.add('hidden');
        } else {
            singleOutputContainer.classList.remove('hidden');
            variationsOutputContainer.classList.add('hidden');
            textOutput.innerHTML = '<p class="loading-text">Weaving words of magic...</p>';
        }

        try {
            // API call to the proxy server
            const response = await fetch('/api/generate-text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt, context, variations })
            });

            const data = await response.json();

            // Handle variations response
            if (variations) {
                // Remove sanitization and timings from raw JSON view so it only shows the variations JSON
                const rawData = { ...data };
                delete rawData.sanitized_prompt;
                delete rawData.timings;
                
                // Show the raw stringified JSON as requested
                rawOutput.innerText = JSON.stringify(rawData, null, 2);
                
                if (data.sanitized_prompt) {
                    document.getElementById('raw-input-display').textContent = prompt;
                    document.getElementById('sanitized-prompt-display').textContent = data.sanitized_prompt;

                    if (data.timings) {
                        document.getElementById('pipeline-timings').innerHTML =
                            `⏱ Sanitize: ${data.timings.sanitization_ms}ms · ` +
                            `Generate: ${data.timings.generation_ms}ms · ` +
                            `Total: ${data.timings.total_ms}ms`;
                    }

                    document.getElementById('sanitization-panel').classList.remove('hidden');
                }
            } else {
                if (data.message) {
                    textOutput.innerHTML = `<p>${data.message.replace(/\n/g, '<br>')}</p>`;
                } else {
                    textOutput.innerHTML = `<p class="error-text">Failed to generate text: ${data.error || 'Unknown error'}</p>`;
                }
            }
        } catch (error) {
            console.error('Text generation failed:', error);
            const errorMsg = '<p class="error-text">Something went wrong. Please check if the Modal text service is deployed.</p>';
            if (variations) {
                rawOutput.innerHTML = errorMsg;
            } else {
                textOutput.innerHTML = errorMsg;
            }
        } finally {
            // Restore UI state
            setLoading(genTextBtn, false);
        }
    });

    // --- Image Generation Logic ---

    /**
     * Image Generation Event Handler
     * 
     * Manages the text-to-image workflow. It updates the DOM to show a shimmer 
     * loading state, sends the prompt to the orchestration layer, and upon success, 
     * injects the returned base64 data URI into an `<img>` tag for display.
     * 
     * @async
     * @listens click
     * @fires fetch
     */
    genImageBtn.addEventListener('click', async () => {
        const prompt = imagePrompt.value.trim();

        if (!prompt) {
            alert('Please enter an image prompt!');
            return;
        }

        // Set UI to loading state
        setLoading(genImageBtn, true);
        imageResultContainer.classList.remove('hidden');
        document.getElementById('image-sanitization-panel').classList.add('hidden');
        imageOutput.innerHTML = '<div class="image-placeholder"><span class="shimmer"></span><p style="position:relative; z-index:1; color: var(--text-muted)">Painting your vision...</p></div>';

        try {
            // API call to the proxy server
            const response = await fetch('/api/generate-image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt })
            });

            const data = await response.json();

            // Populate sanitization panel
            if (data.sanitized_prompt) {
                document.getElementById('image-raw-input-display').textContent = prompt;
                document.getElementById('image-sanitized-prompt-display').textContent = data.sanitized_prompt;

                if (data.timings) {
                    document.getElementById('image-pipeline-timings').innerHTML =
                        `⏱ Sanitize: ${data.timings.sanitization_ms}ms · ` +
                        `Generate: ${data.timings.generation_ms}ms · ` +
                        `Total: ${data.timings.total_ms}ms`;
                }

                document.getElementById('image-sanitization-panel').classList.remove('hidden');
            }

            // Render generated image
            if (data.image_url) {
                imageOutput.innerHTML = `<img src="${data.image_url}" alt="Generated Image" class="animate-in">`;
            } else {
                imageOutput.innerHTML = `<div class="image-placeholder"><p class="error-text">Failed to generate image: ${data.error || 'Unknown error'}</p></div>`;
            }
        } catch (error) {
            console.error('Image generation failed:', error);
            imageOutput.innerHTML = '<div class="image-placeholder"><p class="error-text">Something went wrong. Please check if the Modal image service is deployed.</p></div>';
        } finally {
            // Restore UI state
            setLoading(genImageBtn, false);
        }
    });

    // --- Utility Functions ---

    /**
     * Clipboard Utility Handler
     * 
     * Reads the inner text of the generated output container and writes it to 
     * the system clipboard. Temporarily updates the button text to provide 
     * visual feedback of success.
     * 
     * @listens click
     */
    copyBtn.addEventListener('click', () => {
        const text = textOutput.innerText;
        navigator.clipboard.writeText(text).then(() => {
            const originalText = copyBtn.innerText;
            copyBtn.innerText = 'Copied!';
            setTimeout(() => copyBtn.innerText = originalText, 2000);
        });
    });

    /**
     * Updates the visual loading state of action buttons.
     * 
     * Disables the button to prevent duplicate submissions and toggles the 
     * visibility of the internal text and loading spinner elements.
     * 
     * @param {HTMLElement} btn - The button DOM element to modify.
     * @param {boolean} isLoading - True to set the button to a loading state, false to restore it.
     */
    function setLoading(btn, isLoading) {
        const btnText = btn.querySelector('.btn-text');
        const loader = btn.querySelector('.loader');
        
        if (isLoading) {
            btn.disabled = true;
            btnText.classList.add('hidden');
            loader.classList.remove('hidden');
        } else {
            btn.disabled = false;
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
        }
    }

    // --- Image Edit Logic ---

    const genEditBtn = document.getElementById('gen-edit-btn');
    const editImageUpload = document.getElementById('edit-image-upload');
    const uploadZone = document.getElementById('upload-zone');
    const uploadPlaceholder = document.getElementById('upload-placeholder');
    const editSourcePreview = document.getElementById('edit-source-preview');
    const editPrompt = document.getElementById('edit-prompt');
    const strengthSlider = document.getElementById('strength-slider');
    const strengthValue = document.getElementById('strength-value');
    const editOutput = document.getElementById('edit-output');

    let sourceImageBase64 = null;

    // Strength slider live update
    strengthSlider.addEventListener('input', () => {
        strengthValue.textContent = strengthSlider.value;
    });

    // Click-to-upload
    uploadZone.addEventListener('click', () => editImageUpload.click());

    // Drag & drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) {
            handleImageFile(e.dataTransfer.files[0]);
        }
    });

    // File input change
    editImageUpload.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleImageFile(e.target.files[0]);
        }
    });

    /**
     * File Upload and Base64 Conversion Handler
     * 
     * Validates that the selected file is an image, then uses a FileReader to 
     * asynchronously read the file into a data URL. Updates the preview DOM element 
     * and caches the raw base64 string for later use in API calls.
     * 
     * @param {File} file - The file object originating from an input change or drop event.
     */
    function handleImageFile(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please select a valid image file.');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            // e.target.result is a data URL: "data:image/png;base64,<data>"
            editSourcePreview.src = e.target.result;
            editSourcePreview.classList.remove('hidden');
            uploadPlaceholder.classList.add('hidden');

            // Extract the raw base64 portion (strip the data URL prefix).
            sourceImageBase64 = e.target.result.split(',')[1];
        };
        reader.readAsDataURL(file);
    }

    /**
     * Image Edit (img2img) Event Handler
     * 
     * Orchestrates the image editing workflow. It ensures both a source image 
     * and a prompt are present, sets the DOM to a loading state, and dispatches 
     * the payload to the backend proxy. Upon success, it renders the edited image.
     * 
     * @async
     * @listens click
     * @fires fetch
     */
    genEditBtn.addEventListener('click', async () => {
        const prompt = editPrompt.value.trim();
        const strength = parseFloat(strengthSlider.value);

        if (!sourceImageBase64) {
            alert('Please upload a source image first!');
            return;
        }
        if (!prompt) {
            alert('Please enter an edit instruction!');
            return;
        }

        setLoading(genEditBtn, true);
        document.getElementById('edit-sanitization-panel').classList.add('hidden');
        editOutput.innerHTML = '<div class="image-placeholder"><span class="shimmer"></span><p style="position:relative; z-index:1; color: var(--text-muted)">Applying your edits...</p></div>';

        try {
            const response = await fetch('/api/edit-image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    image_base64: sourceImageBase64,
                    prompt,
                    strength,
                    steps
                }),
            });

            const data = await response.json();

            // Populate sanitization panel
            if (data.sanitized_prompt) {
                document.getElementById('edit-raw-input-display').textContent = prompt;
                document.getElementById('edit-sanitized-prompt-display').textContent = data.sanitized_prompt;

                if (data.timings) {
                    document.getElementById('edit-pipeline-timings').innerHTML =
                        `⏱ Sanitize: ${data.timings.sanitization_ms}ms · ` +
                        `Generate: ${data.timings.generation_ms}ms · ` +
                        `Total: ${data.timings.total_ms}ms`;
                }

                document.getElementById('edit-sanitization-panel').classList.remove('hidden');
            }

            if (data.image_url) {
                editOutput.innerHTML = `<img src="${data.image_url}" alt="Edited Image" class="animate-in">`;
            } else {
                editOutput.innerHTML = `<div class="image-placeholder"><p class="error-text">Edit failed: ${data.error || 'Unknown error'}</p></div>`;
            }
        } catch (error) {
            console.error('Image edit failed:', error);
            editOutput.innerHTML = '<div class="image-placeholder"><p class="error-text">Something went wrong. Please check if the Modal image edit service is deployed.</p></div>';
        } finally {
            setLoading(genEditBtn, false);
        }
    });
});
