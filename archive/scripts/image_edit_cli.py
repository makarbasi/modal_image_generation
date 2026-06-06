"""
Smart Wish AI - Image Edit CLI Client (Administrative Tool)

Interactive terminal tool for testing the img2img editing service
deployed on Modal.

Usage:
    python ai/src/image_edit_cli.py
"""

import modal
import sys
import os
from pathlib import Path


def main():
    print("\n" + "=" * 44)
    print("   🖌️  SMART WISH IMAGE EDITOR (img2img) 🖌️")
    print("=" * 44)

    try:
        print("\n🔗 Connecting to Image Edit Engine on Modal...")

        try:
            editor_cls = modal.Cls.from_name(
                "smart-wish-image-edit", "ImageEditService"
            )
            editor = editor_cls()
        except (modal.exception.NotFoundError, AttributeError):
            print("\n❌ Error: Image Edit Service not found.")
            print("Please deploy first: modal deploy ai/src/image_edit.py")
            return

        print("✅ Connected.\n")

        while True:
            print("-" * 44)

            # 1. Get source image path
            source_path = input(
                "👉 Path to source image (or 'q' to quit):\n> "
            ).strip()
            if source_path.lower() == "q":
                break

            source = Path(source_path)
            if not source.exists() or not source.is_file():
                print(f"❌ File not found: {source_path}")
                continue

            # 2. Get edit instruction
            prompt = input("\n👉 Edit instruction:\n> ").strip()
            if not prompt:
                print("❌ Instruction cannot be empty.")
                continue

            # 3. Get strength
            strength_input = input(
                "\n👉 Strength (0.1–1.0, default 0.75):\n> "
            ).strip()
            strength = float(strength_input) if strength_input else 0.75

            # 4. Output filename
            filename = input(
                "\n👉 Save as? (default: 'edited_output.png'):\n> "
            ).strip()
            if not filename:
                filename = "edited_output.png"
            if not filename.endswith(".png"):
                filename += ".png"

            print(f"\n⏳ Editing image... (strength={strength})")

            try:
                image_bytes = source.read_bytes()
                edited_bytes = editor.edit_image.remote(
                    image_bytes, prompt, strength
                )
                Path(filename).write_bytes(edited_bytes)
                print(f"\n✅ Success! Edited image saved to: {os.path.abspath(filename)}")

                if sys.platform == "darwin":
                    os.system(f"open {filename}")

            except Exception as e:
                print(f"\n❌ Error during editing: {e}")

    except KeyboardInterrupt:
        print("\n\n👋 Exiting.")


if __name__ == "__main__":
    main()
