const request = require('supertest');
const app = require('../api/server');

// Mock global fetch
global.fetch = jest.fn();

describe('Orchestration Server API Tests', () => {
    beforeEach(() => {
        fetch.mockClear();
    });

    describe('POST /api/generate-text', () => {
        it('should handle standard text generation', async () => {
            const mockResponse = { text: 'Happy Birthday!' };
            fetch.mockResolvedValueOnce({
                json: async () => mockResponse,
            });

            const response = await request(app)
                .post('/api/generate-text')
                .send({ prompt: 'Write a birthday card' });

            expect(response.status).toBe(200);
            expect(response.body).toEqual(mockResponse);
            expect(fetch).toHaveBeenCalledTimes(1);
        });

        it('should handle variation text generation (with sanitization)', async () => {
            const mockSanitizationRes = { sanitized_prompt: 'Clean prompt' };
            const mockGenRes = { Professional: 'Pro', casual: 'Cas', loving: 'Lov' };
            
            // First fetch is for sanitization, second is for generation
            fetch
                .mockResolvedValueOnce({ json: async () => mockSanitizationRes })
                .mockResolvedValueOnce({ json: async () => mockGenRes });

            const response = await request(app)
                .post('/api/generate-text')
                .send({ prompt: 'Write a card', variations: true });

            expect(response.status).toBe(200);
            expect(response.body.sanitized_prompt).toBe('Clean prompt');
            expect(response.body.Professional).toBe('Pro');
            expect(fetch).toHaveBeenCalledTimes(2);
        });

        it('should handle fetch errors gracefully', async () => {
            fetch.mockRejectedValueOnce(new Error('Network error'));

            const response = await request(app)
                .post('/api/generate-text')
                .send({ prompt: 'Write a card' });

            expect(response.status).toBe(500);
            expect(response.body).toEqual({ error: 'Service Unavailable' });
        });
    });

    describe('POST /api/generate-image', () => {
        it('should handle image generation with sanitization', async () => {
            const mockSanitizationRes = { sanitized_prompt: 'Clean image prompt' };
            const mockGenRes = { image_url: 'data:image/png;base64,123' };

            fetch
                .mockResolvedValueOnce({ json: async () => mockSanitizationRes })
                .mockResolvedValueOnce({ json: async () => mockGenRes });

            const response = await request(app)
                .post('/api/generate-image')
                .send({ prompt: 'Draw a cat' });

            expect(response.status).toBe(200);
            expect(response.body.sanitized_prompt).toBe('Clean image prompt');
            expect(response.body.image_url).toBe('data:image/png;base64,123');
            expect(fetch).toHaveBeenCalledTimes(2);
        });
    });

    describe('POST /api/edit-image', () => {
        it('should handle image edit with sanitization', async () => {
            const mockSanitizationRes = { sanitized_prompt: 'Clean edit prompt' };
            const mockGenRes = { image_url: 'data:image/png;base64,abc' };

            fetch
                .mockResolvedValueOnce({ json: async () => mockSanitizationRes })
                .mockResolvedValueOnce({ json: async () => mockGenRes });

            const response = await request(app)
                .post('/api/edit-image')
                .send({ image_base64: 'abc', prompt: 'Make it blue' });

            expect(response.status).toBe(200);
            expect(response.body.sanitized_prompt).toBe('Clean edit prompt');
            expect(response.body.image_url).toBe('data:image/png;base64,abc');
            expect(fetch).toHaveBeenCalledTimes(2);
        });
    });
});
