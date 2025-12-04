# -*- coding:utf-8 -*-
import os
import re

# --- Baidu OCR Configuration (Extracted from your existing code) ---
BAIDU_OCR_CONFIG = {
    "APP_ID": "7298408",
    "API_KEY": "NxM6ZNhq9mM5Ck3tPr5zMura",
    "SECRET_KEY": "EZxvX4H54YSAHiPU61utysBOovGPlCZn"
}

# --- Import and Error Handling for Baidu SDK ---
try:
    # We expect 'aip' to be installed (baidu-aip package)
    from aip import AipOcr
except ImportError:
    # Define a dummy class for graceful failure if the SDK is missing.
    class AipOcr:
        def __init__(self, *args, **kwargs):
            self.installed = False
        def basicGeneral(self, *args, **kwargs):
            return {"error_msg": "Baidu OCR SDK (aip) not installed. Please run 'pip install baidu-aip'."}

class OCREngine:
    """
    Handles all core OCR logic using the Baidu OCR SDK.
    This class is completely UI-agnostic and synchronous.
    """
    def __init__(self):
        """Initializes the Baidu OCR client."""
        self.client = self._get_ocr_client()

    def _get_ocr_client(self):
        """Initializes and returns the Baidu OCR client."""
        # Check if the dummy class was used
        if 'AipOcr' in globals() and getattr(AipOcr, 'installed', True) == False:
             return AipOcr()

        client = AipOcr(
            BAIDU_OCR_CONFIG["APP_ID"],
            BAIDU_OCR_CONFIG["API_KEY"],
            BAIDU_OCR_CONFIG["SECRET_KEY"]
        )
        return client

    def ocr_image(self, image_path):
        """
        Performs basic general OCR on the given image path and applies
        specific Chinese text filtering rules.
        """
        if getattr(self.client, 'installed', True) == False:
            return self.client.basicGeneral().get("error_msg")
            
        if not os.path.exists(image_path):
            return f"Error: Image file not found at path: {image_path}"
            
        try:
            # Read the image file as binary data
            with open(image_path, 'rb') as fp:
                image_data = fp.read()
            
            # Call the Baidu API (this is the blocking I/O operation)
            result = self.client.basicGeneral(image_data)
            
            # --- Result Parsing and Custom Filtering Logic ---
            if 'error_code' in result:
                return f"OCR API Error ({result.get('error_code')}): {result.get('error_msg')}"
            
            if "words_result" in result:
                # Concatenate all recognized text first
                raw_text = "\n".join([item["words"] for item in result["words_result"]])
                
                # Filter rule: Keep only Chinese characters and common Chinese punctuation
                # This regex is the one you requested: r'[^\u4e00-\u9fa5。，；：？！""''（）《》【】、—…·]'
                regex = r'[^\u4e00-\u9fa5。，；：？！"\'（）《》【】、—…·]'
                filtered_text = re.sub(regex, '', raw_text)
                
                # Remove empty lines and blank content
                filtered_lines = [line.strip() for line in filtered_text.split('\n') if line.strip()]
                final_text = "\n".join(filtered_lines)
                
                # Success: return the cleaned text
                return final_text
                
            else:
                # No text recognized
                return "Warning: No text recognized in the image."
            
        except Exception as e:
            return f"OCR Processing Error: {str(e)}"
            
# --- Testing Block ---
if __name__ == "__main__":
    print("--- Testing OCREngine Module ---")
    
    # NOTE: This test requires the 'baidu-aip' SDK to be installed
    # To test successfully, replace 'real_test_image.jpg' with a path to a Chinese image.
    test_image_path = "real_test_image.jpg" 
    
    # Create a dummy file if the real test image is not found, 
    # ensuring the os.path.exists() check passes for code testing.
    if not os.path.exists(test_image_path):
        with open(test_image_path, 'wb') as f:
            f.write(b'\x00' * 100) # Write some dummy binary data
        print(f"Created dummy file: {test_image_path}")
        print("NOTE: Using a dummy file will result in an API error but tests initialization.")

    try:
        engine = OCREngine()
        
        # Check for SDK installation error
        if getattr(engine.client, 'installed', True) == False:
            print(f"\nFATAL ERROR: {engine.client.basicGeneral().get('error_msg')}")
            exit()

        print(f"\nAttempting OCR on: {test_image_path}...")
        
        result = engine.ocr_image(test_image_path)
        
        print("\n--- OCR Result ---")
        if result.startswith(("Error:", "Warning:")):
            print(f"Status: {result}")
        else:
            print("Status: Success (or API error during actual call).")
            print("Cleaned Text Output:")
            print("-" * 20)
            print(result)
            print("-" * 20)

    except Exception as e:
        print(f"\nAn unexpected error occurred during testing: {e}")
        
    finally:
        # Clean up the dummy file if it was created
        if os.path.exists(test_image_path) and os.path.getsize(test_image_path) == 100:
            os.remove(test_image_path)
            print(f"\nCleaned up dummy file: {test_image_path}")