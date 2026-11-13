# Voice Awareness — Windows

A small Windows desktop app that monitors microphone speech activity. If no human
speech is detected for the selected interval, the supplied 852 Hz MP3 repeats
until speech is detected.

## Included
- Presets: 10, 20, 30, 40, 50, 60 seconds
- Custom interval in seconds or minutes
- WebRTC Voice Activity Detection (speech-like voice, not simple microphone level)
- Repeating alarm that stops when speech is detected
- Minimize the window to keep monitoring in the background
- Your uploaded tone copied to `assets/852Hz_alarm.mp3`

## Run
1. Install Python 3.10+ for Windows. During setup, enable **Add Python to PATH**.
2. Extract this ZIP to a normal folder.
3. Double-click `RUN_VOICE_AWARENESS.bat`.
4. On first run, it installs the required Python packages.
5. Select an interval and click **START MONITORING**.
6. Minimize the window to keep it running.

## Important behaviour
The interval is a maximum quiet period: speech detected at any point resets the
quiet-period timer. If the timer reaches the selected interval, the MP3 loops.
As soon as speech is detected again, playback stops and the quiet timer resets.
The app does not record or save microphone audio; it processes short audio frames
locally for speech activity detection.

## Windows microphone permission
Go to Settings → Privacy & security → Microphone. Enable microphone access and
desktop-app microphone access. Select the correct input device in Windows.

## Notes / limitations
- This is the runnable Python project/source, not a signed standalone EXE.
- A first run needs internet access to install dependencies.
- WebRTC VAD is designed to identify speech-like voice frames. It may miss very
  quiet speech or classify some noisy sounds as speech.
- If the supplied MP3 is a long track, it loops as a whole file.
- Do not use this as a medical or guaranteed attention/overthinking treatment.
- Use a comfortable listening volume. 852 Hz is not scientifically established
  as a treatment for overthinking; here it is simply your chosen reminder sound.
