#!/usr/bin/env python3
"""
Smart Wish AI - Live E2E Integration Test Suite

This script performs full end-to-end integration tests by making HTTP requests to the
locally running orchestration server (http://localhost:3000). It validates:
1. Text-to-Text: Prompt sanitization + generation of three card variations (professional, casual, loving).
2. Text-to-Image (txt2img): Prompt sanitization + Flux image generation.
3. Image-to-Image (img2img): Prompt sanitization + Flux image editing.

All three pipelines include sequential LLM sanitization and timing telemetry.
"""

import urllib.request
import json
import base64
import time
import os
import sys

GATEWAY_URL = "http://localhost:3000"

def log_section(title):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def post_request(endpoint, payload):
    url = f"{GATEWAY_URL}{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    start_time = time.time()
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            elapsed = time.time() - start_time
            return json.loads(res_body), elapsed, None
    except Exception as e:
        elapsed = time.time() - start_time
        return None, elapsed, str(e)

def test_text_to_text():
    log_section("📝 PIPELINE 1: Text-to-Text (Sanitization + Tonal Variations)")
    
    # Sparse, messy input
    raw_prompt = "Hey AI can u write me a bday card for my coder friend sarah who loves warm coffee"
    print(f"👉 Raw Input Prompt:\n   \"{raw_prompt}\"")
    print("\n⏳ Sending request to Gateway...")
    
    payload = {
        "prompt": raw_prompt,
        "variations": True
    }
    
    data, elapsed, err = post_request("/api/generate-text", payload)
    
    if err:
        print(f"❌ Text-to-Text Request Failed: {err}")
        return False
        
    print(f"✅ Success! (Network Request took {elapsed:.2f}s)")
    print("\n✨ --- SANITIZATION RESULT ---")
    print(f"🧹 Sanitized Prompt:\n   \"{data.get('sanitized_prompt', 'N/A')}\"")
    
    print("\n🎭 --- TONAL VARIATIONS ---")
    print(f"💼 Professional:\n   \"{data.get('Professional', 'N/A')}\"")
    print(f"☕ Casual:\n   \"{data.get('casual', 'N/A')}\"")
    print(f"❤️ Loving:\n   \"{data.get('loving', 'N/A')}\"")
    
    print("\n📊 --- TELEMETRY & TIMINGS ---")
    timings = data.get("timings", {})
    print(f"⏱️  Sanitization Latency: {timings.get('sanitization_ms', 0)} ms")
    print(f"⏱️  Generation Latency:   {timings.get('generation_ms', 0)} ms")
    print(f"⏱️  Total Server Latency: {timings.get('total_ms', 0)} ms")
    
    # Assertions
    assert "sanitized_prompt" in data, "Missing sanitized prompt"
    assert "Professional" in data, "Missing professional variation"
    assert "casual" in data, "Missing casual variation"
    assert "loving" in data, "Missing loving variation"
    print("\n💚 Pipeline 1 Verified Successfully!")
    return True

def test_text_to_image():
    log_section("🎨 PIPELINE 2: Text-to-Image (Sanitization + Flux Generation)")
    
    raw_prompt = "Draw me a picture of a cute kitten sitting in a tea cup"
    print(f"👉 Raw Input Prompt:\n   \"{raw_prompt}\"")
    print("\n⏳ Sending request to Gateway (may take 10-30s if cold booting Modal)...")
    
    payload = {
        "prompt": raw_prompt
    }
    
    data, elapsed, err = post_request("/api/generate-image", payload)
    
    if err:
        print(f"❌ Text-to-Image Request Failed: {err}")
        return None
        
    print(f"✅ Success! (Network Request took {elapsed:.2f}s)")
    
    sanitized = data.get("sanitized_prompt", "N/A")
    print("\n✨ --- SANITIZATION RESULT ---")
    print(f"🧹 Sanitized Prompt:\n   \"{sanitized}\"")
    
    image_url = data.get("image_url", "")
    if not image_url.startswith("data:image/png;base64,"):
        print("❌ Error: Invalid image URL returned.")
        return None
        
    # Extract base64 and save image
    b64_data = image_url.split(",")[1]
    img_bytes = base64.b64decode(b64_data)
    
    output_filename = "tests/e2e/test_kitten.png"
    with open(output_filename, "wb") as f:
        f.write(img_bytes)
        
    print(f"\n🖼️  --- IMAGE OUTPUT ---")
    print(f"💾 Saved generated image to: {os.path.abspath(output_filename)}")
    
    print("\n📊 --- TELEMETRY & TIMINGS ---")
    timings = data.get("timings", {})
    print(f"⏱️  Sanitization Latency: {timings.get('sanitization_ms', 0)} ms")
    print(f"⏱️  Generation Latency:   {timings.get('generation_ms', 0)} ms")
    print(f"⏱️  Total Server Latency: {timings.get('total_ms', 0)} ms")
    
    print("\n💚 Pipeline 2 Verified Successfully!")
    return output_filename

def test_image_to_image(source_image_path):
    log_section("🖌️  PIPELINE 3: Image-to-Image (Sanitization + Flux Edit)")
    
    if not source_image_path or not os.path.exists(source_image_path):
        print("❌ Skipping Image-to-Image E2E test because source image does not exist.")
        return False
        
    with open(source_image_path, "rb") as f:
        img_bytes = f.read()
    image_base64 = base64.b64encode(img_bytes).decode("utf-8")
    
    edit_instruction = "Make the kitten wear a tiny blue wizard hat and add soft sparkles"
    print(f"👉 Source Image: {os.path.basename(source_image_path)}")
    print(f"👉 Edit Prompt:  \"{edit_instruction}\"")
    print("\n⏳ Sending request to Gateway (may take 10-30s)...")
    
    payload = {
        "image_base64": image_base64,
        "prompt": edit_instruction,
        "strength": 0.75,
        "steps": 8
    }
    
    data, elapsed, err = post_request("/api/edit-image", payload)
    
    if err:
        print(f"❌ Image-to-Image Request Failed: {err}")
        return False
        
    print(f"✅ Success! (Network Request took {elapsed:.2f}s)")
    
    sanitized = data.get("sanitized_prompt", "N/A")
    print("\n✨ --- SANITIZATION RESULT ---")
    print(f"🧹 Sanitized Prompt:\n   \"{sanitized}\"")
    
    image_url = data.get("image_url", "")
    if not image_url.startswith("data:image/png;base64,"):
        print("❌ Error: Invalid image URL returned.")
        return False
        
    # Extract base64 and save image
    b64_data = image_url.split(",")[1]
    edited_bytes = base64.b64decode(b64_data)
    
    output_filename = "tests/e2e/test_wizard_kitten.png"
    with open(output_filename, "wb") as f:
        f.write(edited_bytes)
        
    print(f"\n🖼️  --- IMAGE OUTPUT ---")
    print(f"💾 Saved edited image to: {os.path.abspath(output_filename)}")
    
    print("\n📊 --- TELEMETRY & TIMINGS ---")
    timings = data.get("timings", {})
    print(f"⏱️  Sanitization Latency: {timings.get('sanitization_ms', 0)} ms")
    print(f"⏱️  Generation Latency:   {timings.get('generation_ms', 0)} ms")
    print(f"⏱️  Total Server Latency: {timings.get('total_ms', 0)} ms")
    
    print("\n💚 Pipeline 3 Verified Successfully!")
    return True

def main():
    print("=" * 60)
    print(" 🚀 SMART WISH E2E INTEGRATION TEST RUNNER 🚀")
    print("=" * 60)
    print(f"Target Gateway: {GATEWAY_URL}")
    
    # Check gateway availability
    try:
        with urllib.request.urlopen(GATEWAY_URL, timeout=3) as res:
            pass
        print("🟢 Connection to Local Gateway established.")
    except Exception as e:
        print(f"🔴 Error: Cannot connect to local gateway at {GATEWAY_URL}.")
        print("   Make sure the Express server is running (e.g., 'npm start' or running in the background).")
        sys.exit(1)
        
    t2t_success = test_text_to_text()
    
    t2i_image = test_text_to_image()
    
    if t2i_image:
        i2i_success = test_image_to_image(t2i_image)
    else:
        i2i_success = False
        print("\n❌ Skipping Pipeline 3 because Pipeline 2 did not produce an image.")
        
    log_section("🏁 TEST RUN SUMMARY")
    print(f"📝 Text-to-Text: {'✅ PASSED' if t2t_success else '❌ FAILED'}")
    print(f"🎨 Text-to-Image: {'✅ PASSED' if t2i_image else '❌ FAILED'}")
    print(f"🖌️  Image-to-Image: {'✅ PASSED' if i2i_success else '❌ FAILED'}")
    print("=" * 60)
    
    if t2t_success and t2i_image and i2i_success:
        print("\n🎉 ALL E2E INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
