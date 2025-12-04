Mandarin TTS Tool

A user-friendly Mandarin Text-to-Speech (TTS) tool built with Python, supporting full-text audio generation, single-sentence playback, and cross-platform use (Windows & macOS).

Key Features

- Convert any Mandarin text to natural-sounding audio

- Image-to-Text Recognition: Extract clean Mandarin text from images (automatically filters non-Chinese characters and retains only Chinese characters + standard punctuation)

- Dual playback modes: full-text playback or single-sentence playback (double-click to play)

- Customizable voice options (switch between different Mandarin speakers)

- Adjustable speech speed  (-50% slower to 100% faster, 0% for normal speed)

- Flexible playback settings: repeat count adjustment, infinite loop, and custom playback interval

- Clean and intuitive graphical user interface (GUI) – no coding required

- Automatic temporary file management (cleans up unused audio files to save disk space)

- Batch processing: Convert multiple text files to audio in one go

System Requirements

- Windows 10/11 (64-bit)

- macOS 10.15 (Catalina) or later

Installation Guide

For Windows Users

1. Download the MandarinTTS-Windows.exe file from the Releases section or Artifacts

2. Double-click the .exe file to launch the tool directly (no installation required)

3. If your antivirus software flags the file as suspicious:
        Temporarily disable real-time protection

4. Add the .exe file to your antivirus whitelist

For macOS Users

1. Download the MandarinTTS-Mac.dmg file from the Releases section or Artifacts

2. Double-click the .dmg file to mount the disk image

3. Drag the MandarinTTS-Mac.app icon to the Applications folder

4. First-time launch:
        Right-click the app in Applications

5. Select Open from the menu

6. Click Open again in the pop-up window (to bypass "unidentified developer" warning)

How to Use

Basic Text-to-Speech

1. Launch the Mandarin TTS Tool

2. In the left text box, input or paste the Mandarin text you want to convert

3. Select your preferred voice from the Voice dropdown menu

4. Adjust speech speed using the slider (-50% to 100%, 0% is normal speed)

5. Click Process Text & Generate Audio (wait for 2-5 seconds, depending on text length)

6. After processing:
        Use ▶ Play/⏸ Pause/■ Stop buttons to control full-text playback

7. Double-click any sentence in the right list to play that single sentence

8. Optional settings:
        Mode: Switch between "Single" (play selected sentence repeatedly) or "Full" (play entire text)

9. Repeat: Set playback count (check "Loop" for infinite playback)

10. Interval: Adjust the interval between repeated playbacks (in milliseconds)

Image-to-Text Recognition
1. Click Select Image for OCR in the status bar (top-right)

2. Choose an image file (supports .png, .jpg, .jpeg, .bmp, .gif) containing Mandarin text

3. Wait for recognition (a progress window will appear)

4. The extracted text (cleaned to retain only Chinese characters and punctuation) will automatically populate the left text box

5. Follow steps 3-6 in the "Basic Text-to-Speech" section to generate audio

Optional Settings
1. Mode: Switch between "Single" (play selected sentence repeatedly) or "Full" (play entire text)

2. Repeat: Set playback count (check "Loop" for infinite playback)

3. Interval: Adjust the interval between repeated playbacks (in milliseconds)


Important Notes

- After switching to a new voice, you must click Process Text & Generate Audio again for the change to take effect

- If you encounter "missing DLL" errors on Windows: Install Microsoft Visual C++ Redistributable (64-bit)

- The tool requires an internet connection for the first use (to initialize TTS engine)

- Avoid inputting extremely long texts (over 1000 characters) for better performance

Troubleshooting

- Audio not playing: Check if your system volume is muted; try restarting the tool

- App crashes on launch: Ensure your system meets the minimum requirements; re-download the latest version from Releases

- Slow processing: Reduce text length or close other heavy applications

- Image recognition failures: Try with a higher-quality image or manually type text into the input box

Contact

For bug reports or feature requests, please open an issue in the GitHub repository.
