# Soundbox

A keyboard-controlled sound player that allows you to trigger multiple overlapping audio samples from the terminal. Perfect for DJs, sound designers, producers, and anyone who needs quick keyboard-triggered audio playback.

## Features

- **36 keyboard hotkeys** - Trigger sounds with keys 0-9 and a-z
- **Overlapping playback** - Play up to 8 simultaneous audio samples
- **Pagination** - Page through your entire audio library (36 sounds per page)
- **Fade control** - Smooth fade-out for the most recently played track
- **Multiple audio formats** - Support for MP3, WAV, AIFF, FLAC, OGG, AAC, and M4A
- **Quick interruption** - Stop all sounds with a single key press
- **Global keyboard capture** - Responds to keypresses even when the terminal isn't in focus

## Requirements

- Python 3.6+
- pygame
- keyboard
- Linux/Unix system (for elevated keyboard access)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/soundbox.git
cd soundbox
```

2. Install dependencies:
```bash
pip install pygame keyboard
```

3. Organize your audio files:
   - Place audio files in a directory (or multiple subdirectories)
   - Supported formats: `.mp3`, `.wav`, `.aiff`, `.flac`, `.ogg`, `.aac`, `.m4a`

## Usage

Run the program with your audio directory:

```bash
export SOUND_FILE_PATH=/path/to/your/audio/files
python soundbox.py
```

Then enter your password when prompted (required for global keyboard access).

### Keyboard Controls

| Key | Action |
|-----|--------|
| **0-9, a-z** | Play audio file assigned to that key |
| **Press key again** | Fade out the sound (after 1+ second of playback) |
| **↑ Arrow** | Go to previous page |
| **↓ Arrow** | Go to next page |
| **TAB** | Fade out the most recently played track |
| **Delete** | Stop all sounds immediately |
| **ESC** | Exit the program |

### Configuration

#### Audio Directory

Set the audio directory via environment variable:
```bash
export SOUND_FILE_PATH=/path/to/audio
```

If not set, defaults to the current working directory.

#### Password Authentication

The program requires sudo access to capture global keyboard input. You can provide your password via:
- Interactive prompt when you run the program
- Environment variable: `export KEYBOARD_ACCESS_PASSWORD="yourpassword"`

## Directory Structure Example

```
soundbox/
├── soundbox.py
├── README.md
└── samples/
    └── 182395__pgonsilva__big-dog-bark-01.aiff
```

## How It Works

1. **Initialization** - Reads all audio files from the specified directory and creates a sorted list
2. **Menu Display** - Shows 36 audio files per page with key assignments (0-9, a-z)
3. **Global Keyboard Listener** - Runs as an elevated subprocess to capture all keyboard events
4. **Channel Management** - Distributes sounds across 8 mixer channels using round-robin assignment
5. **Playback Control** - Allows overlapping sounds, with fade-out and interrupt capabilities

## Technical Details

### Audio Channels

The program supports up to 8 simultaneous audio streams using pygame's mixer channels. Sounds are assigned to channels in a round-robin fashion, so the oldest sound may be interrupted if you exceed 8 overlapping playbacks.

### Keyboard Access

Due to Linux security restrictions, global keyboard capture requires elevated privileges. The program uses `sudo` to run a keyboard listener subprocess that captures all key events system-wide.

### Fade-Out Mechanism

Tracks fade out smoothly over 1 second through 20 volume reduction steps, preventing jarring audio cutoffs.

## Sample Audio Files

This repository includes 37 sample audio files from freesound.org to help you get started quickly. All samples are licensed under Creative Commons 0 (CC0 1.0 Universal), which means they are in the public domain and free to use without attribution.

For a complete list of sample files and their sources, see [samples/license.txt](samples/license.txt).

To use your own audio files instead, simply set the `SOUND_FILE_PATH` environment variable to point to your custom sounds directory.

## Troubleshooting

### "Failed to initialize keyboard listener"
- Ensure you entered the correct password
- Check that the `keyboard` Python module is installed
- Verify you're on a Linux/Unix system

### No audio files found
- Verify the `SOUND_FILE_PATH` environment variable is set correctly
- Ensure your audio files have supported extensions
- Check that the directory path is correct

### Permission denied errors
- The program requires sudo access for keyboard monitoring
- You may need to run the program with appropriate permissions or add your user to sudoers

## License

This project is open source and available under the MIT License.

## Credits

- Built with [pygame](https://www.pygame.org/) for audio mixing
- Global keyboard access via [keyboard](https://github.com/boppreh/keyboard) module

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.
