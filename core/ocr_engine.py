# -*- coding:utf-8 -*-
import os
import re
import sys

# --- Baidu OCR Configuration (Extracted from your existing code) ---
BAIDU_OCR_CONFIG = {
    "APP_ID": "7298408",
    "API_KEY": "NxM6ZNhq9mM5Ck3tPr5zMura",
    "SECRET_KEY": "EZxvX4H54YSAHiPU61utysBOovGPlCZn"
}

# --- Platform-aware Import and Error Handling for Baidu SDK ---
BAIDU_OCR_AVAILABLE = False

if sys.platform == "win32":
    # 只在 Windows 平台尝试导入
    try:
        from aip import AipOcr
        BAIDU_OCR_AVAILABLE = True
    except ImportError:
        # Windows 上 baidu-aip 未安装
        class AipOcr:
            def __init__(self, *args, **kwargs):
                pass
            def basicGeneral(self, *args, **kwargs):
                return {"error_msg": "Baidu OCR SDK (aip) not installed. Please run 'pip install baidu-aip'."}
else:
    # macOS/Linux: 直接定义 dummy class
    class AipOcr:
        def __init__(self, *args, **kwargs):
            pass
        def basicGeneral(self, *args, **kwargs):
            return {"error_msg": f"Baidu OCR is only supported on Windows. Current platform: {sys.platform}"}


class OCREngine:
    """
    Handles all core OCR logic using the Baidu OCR SDK.
    This class is completely UI-agnostic and synchronous.
    
    Platform Support:
    - Windows: Full OCR support with baidu-aip
    - macOS/Linux: Returns platform not supported error
    """
    def __init__(self):
        """Initializes the Baidu OCR client."""
        self.client = self._get_ocr_client()
        self.is_available = BAIDU_OCR_AVAILABLE

    def _get_ocr_client(self):
        """Initializes and returns the Baidu OCR client."""
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
        
        Returns:
            str: OCR result text or error message
        """
        # 首先检查平台支持
        if not BAIDU_OCR_AVAILABLE:
            return f"Error: OCR is only supported on Windows platform (current: {sys.platform})"
            
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
            
            if 'error_msg' in result and not 'words_result' in result:
                return f"Error: {result.get('error_msg')}"
            
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
    print(f"Platform: {sys.platform}")
    print(f"Baidu OCR Available: {BAIDU_OCR_AVAILABLE}")
    
    # NOTE: This test requires the 'baidu-aip' SDK to be installed on Windows
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
        
        print(f"\nOCR Engine initialized. Available: {engine.is_available}")
        print(f"Attempting OCR on: {test_image_path}...")
        
        result = engine.ocr_image(test_image_path)
        
        print("\n--- OCR Result ---")
        if result.startswith(("Error:", "Warning:")):
            print(f"Status: {result}")
        else:
            print("Status: Success")
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