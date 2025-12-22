# -*- coding:utf-8 -*-
import os
import sys
import re
import hashlib
import asyncio
import edge_tts
import time
import shutil

# --- Configuration and Globals ---
VOICE_DICT = {
    "Mandarin Female (Xiaoyi)": "zh-CN-XiaoyiNeural",
    "Mandarin Female (Xiaoxiao)": "zh-CN-XiaoxiaoNeural",
    "Mandarin Female (Yunxi)": "zh-CN-YunxiNeural",
    "Mandarin Male (Yunjian)": "zh-CN-YunjianNeural",
    "Mandarin Male (YunyangNeural)": "zh-CN-YunyangNeural",
}

AUDIO_DIR = "audio_cache"

# Ensure the cache directory exists at initialization
os.makedirs(AUDIO_DIR, exist_ok=True)

class TTSEngine:
    """
    Handles all core Text-to-Speech logic using the edge-tts library.
    Manages text splitting, caching, and audio generation.
    """
    def __init__(self, audio_dir=AUDIO_DIR, clear_cache_on_start=True):
        if getattr(sys, 'frozen', False):
            # 打包后的环境：建议指向用户库或文档目录
            user_data_dir = os.path.expanduser("~/Library/Application Support/MandarinTTS")
            self._audio_dir = os.path.join(user_data_dir, AUDIO_DIR)
        else:
            # 开发环境：使用当前目录
            self._audio_dir = AUDIO_DIR

        if not os.path.exists(self._audio_dir):
            os.makedirs(self._audio_dir, exist_ok=True)
 
        # Clear cache on initialization if requested
        if clear_cache_on_start:
            self._clear_cache()
    
    def _clear_cache(self):
        """
        Clears all cached audio files in the audio directory.
        Keeps the directory itself intact.
        """
        try:
            if os.path.exists(self._audio_dir):
                for filename in os.listdir(self._audio_dir):
                    file_path = os.path.join(self._audio_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print(f"Warning: Failed to delete {file_path}: {e}")
                print(f"Cache cleared: {self._audio_dir}")
        except Exception as e:
            print(f"Warning: Failed to clear cache directory: {e}")
        
    def text_to_sentences(self, text):
        """
        Splits text into sentences using common Chinese punctuation as delimiters.
        """
        if not text:
            return []
            
        delimiters = r'[。？！；]'
        sentences = re.split(delimiters, text)
        
        # Clean up and re-append delimiters to the sentence fragment
        result = []
        text_to_consume = text 
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                
                sentence_start_index = text_to_consume.find(sentence)
                if sentence_start_index == -1:
                    continue

                delimiter_search_area = text_to_consume[sentence_start_index + len(sentence):]
                match = re.search(delimiters, delimiter_search_area)
                delimiter = match.group(0) if match else ''
                
                result.append(sentence + delimiter)
                
                if match:
                    delimiter_end_index = delimiter_search_area.find(delimiter) + len(delimiter)
                    text_to_consume = delimiter_search_area[delimiter_end_index:]
                else:
                    text_to_consume = ""
             
        return [s.strip() for s in result if s.strip()]

    def _get_safe_text(self, text):
        """
        Generates a unique, cache-friendly filename part using SHA1 hash of the text.
        """
        normalized_text = "".join(text.split())
        return hashlib.sha1(normalized_text.encode('utf-8')).hexdigest()

    async def _async_generate(self, text, voice, rate, filepath):
        """
        The asynchronous core function that calls edge-tts to generate and save audio.
        """
        rate_str = f"{rate:+d}%" if isinstance(rate, int) else f"{rate}%"
        communicate = edge_tts.Communicate(text, voice, rate=rate_str)
        await communicate.save(filepath)

    def _get_audio_file_path(self, text, voice, rate, prefix="full"):
        """Helper to generate consistent audio file paths."""
        voice_key = voice.replace('-', '_')
        safe_hash = self._get_safe_text(text)
        filename = f"{prefix}_{voice_key}_{rate}_{safe_hash}.mp3"
        return os.path.join(self._audio_dir, filename)
        
    # --- Public API for Full Text (Thread 2) ---
    def generate_full_audio(self, text, voice, rate):
        """
        Generates the full audio file (or retrieves from cache).
        Designed to be called synchronously from a worker thread.
        
        Returns:
            tuple: (audio_filepath: str, sentence_list: list)
        """
        if not text.strip():
            return "Error: Input text is empty.", []

        sentences = self.text_to_sentences(text)
        full_text_clean = "".join(sentences)
        
        cached_path = self._get_audio_file_path(full_text_clean, voice, rate, prefix="full")

        if os.path.exists(cached_path):
            print(f"TTS Full Cache Hit: Found audio at {cached_path}")
            return cached_path, sentences
        
        print(f"TTS Full Cache Miss: Generating new audio to {cached_path}")
        
        try:
            # Synchronously run the async generation
            asyncio.run(self._async_generate(full_text_clean, voice, rate, cached_path))
            return cached_path, sentences
        except Exception as e:
            return f"Error: TTS Generation Failed: {str(e)}", []
            
    # --- Internal Async for Single Sentence (Used by both Thread 3 and Thread 4) ---
    async def _async_process_single_sentence(self, sentence, voice, rate):
        """Asynchronously checks cache and generates single sentence audio."""
        if not sentence.strip():
            return "Error: Input sentence is empty."

        cached_path = self._get_audio_file_path(sentence, voice, rate, prefix="single")

        if os.path.exists(cached_path):
            return cached_path
        
        # Cache Miss - Generate Audio
        # Note: Printing during batch runs will slow down logging but is kept for clarity
        print(f"TTS Single Cache Miss: Generating new single audio to {cached_path}")
        
        try:
            await self._async_generate(sentence, voice, rate, cached_path)
            return cached_path
        except Exception as e:
            return f"Error: TTS Generation Failed: {str(e)}"

    # --- Public API for Single Sentence (Thread 3) ---
    def generate_single_sentence_audio(self, sentence, voice, rate):
        """
        Synchronous wrapper for single sentence processing (for immediate playback).
        
        Returns:
            str: audio_filepath or Error string
        """
        return asyncio.run(self._async_process_single_sentence(sentence, voice, rate))
        
    # --- Public API for Batch Processing (Thread 4) ---
    async def process_all_sentences(self, sentences, voice, rate):
        """
        Asynchronously processes and caches audio for an entire list of sentences CONCURRENTLY.
        
        Returns:
            bool: True on success, False if any sentence generation failed.
        """
        if not sentences:
            return True
        
        print(f"Starting concurrent batch generation for {len(sentences)} sentences...")
        
        tasks = [self._async_process_single_sentence(s, voice, rate) for s in sentences]
        
        # Run all generation tasks concurrently using asyncio.gather
        results = await asyncio.gather(*tasks)
        
        # Check results
        success = True
        for i, result in enumerate(results):
            if result.startswith("Error"):
                print(f"Error during pre-caching sentence {i+1}: {result}")
                success = False
                
        return success


# --- Testing Block ---
if __name__ == "__main__":
    print("--- Testing TTSEngine Module ---")
    
    # Setup
    # *** USER'S TEST TEXT CONTENT ***
    test_text = """
我想谈一谈中国在过去四十年中的非凡发展。我选择这个主题，是因为中国如今在许多领域已经成为世界领军者，尤其是在经济和科技方面。我也希望讨论一下促成这一成功的一些原因。首先需要理解的是，四十年前的中国还是一个非常贫穷的国家，许多人生活在贫困线以下。当时的主要产业是农业。政府 认识到，为了与其他国家竞争，中国必须实现发展。因此，在世纪年代初，政府决定进行一系列经济改革。政府大力投资基础设施，升级或新建了许多设施，例如北京新机场和公路网络。如今，中国拥有世界上最大的高速铁路网络，使主要城市之间的连接变得非常快捷和便利。人员和货物能够快速在全国流 动，从而创造大量就业机会。这些资金来自享受特别经济区税收优惠的外国投资者。政府也在人民身上投入，尤其是在教育和性别平等方面。例如，中国如今拥有一些世界顶尖的大学。技术创新是中国迅速发展的主要原因之大型外国公司若想在华投资，必须分享其技术；而中国企业也获得政府的财政支持。科技研究与创新受到鼓励，所有这些都推动了中国的快速发展
    """.strip()
    
    # Use the first sentence for single test
    test_sentence = "我想谈一谈中国在过去四十年中的非凡发展。"
    
    test_voice = VOICE_DICT["Mandarin Female (Xiaoxiao)"]
    test_rate = 0
    test_engine = TTSEngine(audio_dir="test_audio_cache")
    
    # Ensure test directory exists
    os.makedirs(test_engine._audio_dir, exist_ok=True)
    
    print(f"Test Voice: {test_voice}")

    # 1. Test Sentence Split
    print("\n1. Testing Sentence Splitting:")
    sentences = test_engine.text_to_sentences(test_text)
    print(f"Total Sentences: {len(sentences)}")
    for i, s in enumerate(sentences):
        print(f"  [{i+1}] {s}")
    
    # --- Full Text Tests ---
    print("\n2. Testing Full Audio Generation (Cache Miss):")
    start_time_full = time.time()
    path1, list1 = test_engine.generate_full_audio(test_text, test_voice, test_rate)
    end_time_full = time.time()
    print(f"Full Path 1: {path1}")
    print(f"Full Time Taken: {end_time_full - start_time_full:.2f}s")

    print("\n3. Testing Full Audio Retrieval (Cache Hit):")
    start_time_cache = time.time()
    path2, list2 = test_engine.generate_full_audio(test_text, test_voice, test_rate)
    end_time_cache = time.time()
    print(f"Full Path 2: {path2}")
    print(f"Cache Time Taken: {end_time_cache - start_time_cache:.2f}s")
    
    # --- Single Sentence Tests ---
    print("\n4. Testing Single Sentence Generation (Cache Miss):")
    start_time_single = time.time()
    path3 = test_engine.generate_single_sentence_audio(test_sentence, test_voice, test_rate)
    end_time_single = time.time()
    print(f"Single Path 1: {path3}")
    print(f"Single Time Taken: {end_time_single - start_time_single:.2f}s")
    
    print("\n5. Testing Single Sentence Retrieval (Cache Hit):")
    start_time_single_cache = time.time()
    path4 = test_engine.generate_single_sentence_audio(test_sentence, test_voice, test_rate)
    end_time_single_cache = time.time()
    print(f"Single Path 2: {path4}")
    print(f"Single Cache Time Taken: {end_time_single_cache - start_time_single_cache:.2f}s")
    
    
    print("\n6. Testing Batch Sentence Processing CONCURRENTLY (Cache Miss for singles):")
    start_time_batch = time.time()
    batch_success_1 = asyncio.run(test_engine.process_all_sentences(sentences, test_voice, test_rate))
    end_time_batch = time.time()
    print(f"Batch Processing Success (1): {batch_success_1}")
    print(f"Batch Time Taken (1): {end_time_batch - start_time_batch:.2f}s")

    # 3. Test Batch Processing CONCURRENTLY (Cache Hit for individual sentences)
    print("\n7. Testing Batch Sentence Processing CONCURRENTLY (Cache Hit for singles):")
    start_time_batch_cache = time.time()
    batch_success_2 = asyncio.run(test_engine.process_all_sentences(sentences, test_voice, test_rate))
    end_time_batch_cache = time.time()
    print(f"Batch Processing Success (2): {batch_success_2}")
    print(f"Batch Time Taken (2): {end_time_batch_cache - start_time_batch_cache:.2f}s")


    # Final Verification
    print("\n--- Final Verification ---")
    if path1.startswith("Error") or path3.startswith("Error"):
        print("Status: FAILED. TTS Engine reported an error during generation.")
    elif path1 == path2 and path3 == path4 and (end_time_cache - start_time_cache) < 0.5:
        print("Status: SUCCESS. Full and Single TTS logic is sound, and caching works efficiently.")
    else:
        print("Status: FAILED. Path mismatch or slow cache retrieval detected.")
        
    if not batch_success_1 or not batch_success_2:
        print("Status: FAILED. Batch processing reported an error.")
    elif (end_time_batch_cache - start_time_batch_cache) < 0.5:
        print("Status: SUCCESS. Batch processing is fast on cache hit, confirming concurrent pre-generation worked.")
    else:
        print("Status: FAILED. Cache retrieval was slow.")
        

    # Cleanup (Optional)
    # shutil.rmtree("test_audio_cache")
    # print("\nCleaned up test_audio_cache directory.")