"""
Smart Wish AI - Image Generation CLI Client (Administrative Tool)

Provides an interactive terminal interface for low-level testing and 
administrative interaction with the deployed Visual Engine on Modal.
"""

import modal
import sys
import os
from pathlib import Path

def main():
    """
    Main entry point for the interactive image client.
    Connects to the 'smart-wish-image' Modal app and handles the generation request loop.
    
    Pre-requisite: 'modal deploy ai/src/image_gen.py' must be run first.
    """
    print("\n" + "="*40)
    print("   🎨 SMART WISH IMAGE GENERATOR 🎨")
    print("="*40)

    try:
        print("\n🔗 Connecting to Flux Engine on Modal...")
        
        # Initialize connection to the deployed Modal class
        try:
            generator_cls = modal.Cls.from_name("smart-wish-image", "ImageService")
            generator = generator_cls()
        except (modal.exception.NotFoundError, AttributeError):
            print("\n❌ Error: Image Service not found.")
            print("Please deploy the service first: modal deploy ai/src/image_gen.py")
            return

        print("✅ Connected.")

        # Interactive loop
        while True:
            print("\n" + "-"*40)
            prompt = input("👉 Describe the image you want (or 'q' to quit):\n> ").strip()
            
            if prompt.lower() == 'q':
                break
            if not prompt:
                continue

            # Optional output filename
            filename = input("\n👉 Save as? (e.g. graduation.png, or press Enter for 'output.png'):\n> ").strip()
            if not filename:
                filename = "output.png"
            if not filename.endswith(".png"):
                filename += ".png"

            print(f"\n⏳ Generating '{filename}'... (This takes ~15-30s)")
            
            try:
                # Call the remote method on Modal
                image_bytes = generator.generate_image.remote(prompt)
                
                # Write raw bytes to local filesystem
                Path(filename).write_bytes(image_bytes)
                print(f"\n✅ Success! Image saved to: {os.path.abspath(filename)}")
                
                # Automatically open the image on macOS for immediate preview
                if sys.platform == "darwin":
                    os.system(f"open {filename}")

            except Exception as e:
                print(f"\n❌ An error occurred during generation: {e}")

    except KeyboardInterrupt:
        print("\n\n👋 Exiting.")

if __name__ == "__main__":
    main()
