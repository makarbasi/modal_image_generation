"""
Smart Wish AI - Text Generation CLI Client (Administrative Tool)

Provides an interactive terminal interface for low-level testing and 
administrative interaction with the deployed Text Engine on Modal.
"""

import modal
import sys

def main():
    """
    Main entry point for the interactive text client.
    Connects to the 'smart-wish-text' Modal app and handles the user input loop.
    
    Pre-requisite: 'modal deploy ai/src/text_gen.py' must be run first.
    """
    print("\n" + "="*40)
    print("   🌟 SMART WISH AI REMOTE CLIENT 🌟")
    print("="*40)

    try:
        print("\n🔗 Connecting to Smart Wish AI on Modal...")
        
        # Initialize connection to the deployed Modal class
        try:
            assistant_cls = modal.Cls.from_name("smart-wish-text-v2", "TextService")
            assistant = assistant_cls()
        except (modal.exception.NotFoundError, AttributeError):
            print("\n❌ Error: AI Service not found.")
            print("Please deploy the service first: modal deploy ai/src/text_gen.py")
            return

        print("✅ Connected.")

        # Interactive loop
        while True:
            print("\n" + "-"*40)
            user_request = input("👉 What kind of message should I write? (or 'q' to quit)\n> ").strip()
            
            if user_request.lower() == 'q':
                break
            if not user_request:
                continue

            user_context = input("\n👉 Any extra details? (or press Enter to skip)\n> ").strip()

            print("\n⏳ Generating message...")
            
            # Call the remote method on Modal
            response = assistant.generate_message.remote(
                user_request=user_request, 
                context=user_context if user_context else None
            )

            print("\n" + "✨" + "-"*38 + "✨")
            print("           GENERATED MESSAGE")
            print("-" * 40)
            print(f"\n{response}\n")
            print("=" * 40)

    except KeyboardInterrupt:
        print("\n\n👋 Exiting client.")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
