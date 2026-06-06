import modal
import sys

import sys
import os

# Import the modal app and TextService from text_gen.py
# We can invoke it locally for testing using Modal's local execution.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../core')))
from text_gen import TextService, app

@app.local_entrypoint()
def test_pipeline():
    print("🚀 Running Sanitization Pipeline Tests on Modal...")
    service = TextService()
    
    test_cases = [
        {
            "name": "Conversational filler",
            "input": "Hey AI can you write me a birthday card for my dad",
            "forbidden": ["Hey AI", "can you", "write me"]
        },
        {
            "name": "Typos & grammar",
            "input": "hapyy aniversary to my wife sarah shes the best",
            "expected": ["anniversary", "Sarah"]
        },
        {
            "name": "Sparse/vague input",
            "input": "birthday card for dad",
            "check": lambda i, o: len(o) > len(i)
        },
        {
            "name": "Already clean input",
            "input": "A warm birthday greeting for my father who loves gardening.",
            "check": lambda i, o: "gardening" in o.lower()
        }
    ]
    
    success = True
    
    for case in test_cases:
        print(f"\n--- Test: {case['name']} ---")
        print(f"Input: {case['input']}")
        
        # Call the remote method
        output = service.sanitize_input.remote(case['input'])
        print(f"Output: {output}")
        
        if "forbidden" in case:
            for word in case["forbidden"]:
                if word.lower() in output.lower():
                    print(f"❌ Failed: Output contains forbidden phrase '{word}'")
                    success = False
        
        if "expected" in case:
            for word in case["expected"]:
                if word.lower() not in output.lower():
                    print(f"❌ Failed: Output missing expected word '{word}'")
                    success = False
                    
        if "check" in case:
            if not case["check"](case['input'], output):
                print(f"❌ Failed: Custom check failed")
                success = False

    # Image sanitization tests
    print("\n🚀 Running Image Sanitization Tests on Modal...")
    image_test_cases = [
        {
            "name": "Image Conversational filler",
            "input": "Draw me a picture of a cute puppy playing in the snow",
            "forbidden": ["Draw me", "a picture of", "can you"]
        },
        {
            "name": "Image Sparse/vague input",
            "input": "a dog",
            "check": lambda i, o: len(o) > len(i) and ("dog" in o.lower() or "retriever" in o.lower() or "puppy" in o.lower())
        }
    ]

    for case in image_test_cases:
        print(f"\n--- Image Test: {case['name']} ---")
        print(f"Input: {case['input']}")
        
        output = service.sanitize_image_input.remote(case['input'])
        print(f"Output: {output}")
        
        if "forbidden" in case:
            for word in case["forbidden"]:
                if word.lower() in output.lower():
                    print(f"❌ Failed: Output contains forbidden phrase '{word}'")
                    success = False
                    
        if "check" in case:
            if not case["check"](case['input'], output):
                print(f"❌ Failed: Custom check failed")
                success = False

    if success:
        print("\n✅ All sanitization tests passed!")
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    print("Run this script using: modal run test_sanitization.py")
