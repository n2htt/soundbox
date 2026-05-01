import time
import os
import pygame
import subprocess
import sys
import json
import getpass
import termios
import select

first_menu = True
keyboard_process = None
interrupt_playback = False
channels = None
channel_index = 0
playing_keys = {}  # Dictionary mapping keys to their assigned channels
current_page = 0  # Track current page
total_pages = 1   # Total number of pages
page_offset = 0   # Offset of first file on current page
last_channel_used = None  # Track the most recently played channel

def create_keylist():
    """Create a dictionary mapping keys (0-9, a-z) to positions on a page."""
    keylist = {}
    for i in range(36):
        if i < 10:
            key = str(i)
        else:
            key = chr(ord('a') + (i - 10))
        keylist[key] = i
    return keylist

def fade_out_channel(channel, duration=1.0):
    """Fade out a channel over the specified duration (in seconds), then stop it."""
    if not channel.get_busy():
        return
    
    steps = 20  # Number of volume reduction steps
    step_duration = duration / steps
    initial_volume = channel.get_volume()
    
    for i in range(steps):
        volume = initial_volume * (1 - (i + 1) / steps)
        channel.set_volume(volume)
        time.sleep(step_duration)
    
    channel.stop()
    channel.set_volume(initial_volume)  # Reset volume for next playback

def start_keyboard_listener(password, keylist_keys):
    """Start keyboard listener as elevated subprocess."""
    global keyboard_process
    
    # Python code to run as elevated process
    listener_code = """
import keyboard
import sys
import json

try:
    keylist = json.loads(sys.argv[1])
    
    while True:
        try:
            event = keyboard.read_event()
            
            if event.event_type == keyboard.KEY_DOWN:
                if event.name == 'esc':
                    print("ESC", flush=True)
                elif event.name == 'delete':
                    print("DELETE", flush=True)
                elif event.name == 'down':
                    print("DOWN", flush=True)
                elif event.name == 'up':
                    print("UP", flush=True)
                elif event.name == 'tab':
                    print("TAB", flush=True)
                elif event.name in keylist:
                    print(event.name, flush=True)
        except Exception as e:
            print(f"ERROR: {e}", flush=True)
except Exception as e:
    print(f"INIT_ERROR: {e}", flush=True)
    sys.exit(1)
"""
    
    try:
        # Start subprocess with sudo
        keyboard_process = subprocess.Popen(
            ['sudo', '-S', 'python3', '-c', listener_code, json.dumps(keylist_keys)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Send password on first line
        keyboard_process.stdin.write(password + '\n')
        keyboard_process.stdin.flush()
        
        return keyboard_process
    except Exception as e:
        print(f"Failed to start keyboard listener: {e}")
        return None

def get_password():
    """Get password from environment variable or prompt user."""
    password = os.environ.get('KEYBOARD_ACCESS_PASSWORD')
    if password:
        return password
    return getpass.getpass('Enter password for keyboard access: ')

def present_dynamic_menu(keylist, audio_files):
    """Present the menu with dynamic key assignments for the current page."""
    global first_menu, current_page, total_pages, page_offset
    os.system('clear' if os.name != 'nt' else 'cls')
    if first_menu:
        print("Welcome to the Soundbox!")
        first_menu = False
    
    print(f"Page {current_page + 1} of {total_pages}")
    print()
    
    # Calculate which files to display for this page
    start_idx = page_offset
    end_idx = min(start_idx + 36, len(audio_files))
    
    for key, position in keylist.items():
        file_idx = start_idx + position
        if file_idx < end_idx:
            filename = audio_files[file_idx]
            print(f"  {key} - {os.path.basename(filename)}")
    
    print()
    print("↑/↓ - change pages | TAB - fade out current track")
    print("DEL - interrupt playback")
    print("ESC - exit")

def is_key_playing(key):
    """Check if a key's sound is currently playing."""
    if key in playing_keys:
        channel = playing_keys[key]
        return channel.get_busy()
    return False

def pressed_it(kn, audio_files):
    global channel_index, playing_keys, page_offset, keylist, last_channel_used
    time.sleep(0.01)
    os.system('clear' if os.name != 'nt' else 'cls')
    
    # Calculate the actual file index based on current page and key position
    file_idx = page_offset + keylist[kn]
    filename = audio_files[file_idx]
    print(f"\nPlaying file {file_idx}: {os.path.basename(filename)}")
    
    # Load and play sound on next available channel using round-robin
    sound = pygame.mixer.Sound(filename)
    channels[channel_index].play(sound)
    playing_keys[kn] = channels[channel_index]  # Track which channel this key is using
    last_channel_used = channels[channel_index]  # Track the most recently played channel
    channel_index = (channel_index + 1) % len(channels)
    
    # Return immediately - sound plays in background
    time.sleep(0.3)
    os.system('clear' if os.name != 'nt' else 'cls')
    present_dynamic_menu(keylist, audio_files)

pygame.mixer.init()
channels = [pygame.mixer.Channel(i) for i in range(8)]  # Support up to 8 overlapping sounds
time.sleep(0.1)
os.system('clear' if os.name != 'nt' else 'cls')

# Get sound file directory from environment variable, default to current directory
sound_dir = os.environ.get('SOUND_FILE_PATH', '.')

# Read file names from the sound directory and filter by audio extensions
audio_extensions = ('mp3', 'wav', 'off', 'aiff', 'flac', 'ogg', 'aac', 'm4a')
audio_files = []
for filename in os.listdir(sound_dir):
    if filename.lower().endswith(audio_extensions):
        audio_files.append(os.path.join(sound_dir, filename))

if not audio_files:
    print("No audio files found in the current directory.")
    exit()  

audio_files.sort()
keylist = create_keylist()

# Calculate total pages
total_pages = (len(audio_files) + 35) // 36  # Ceiling division
page_offset = 0
current_page = 0

password = get_password()

# Start keyboard listener with elevated privilege 
keyboard_process = start_keyboard_listener(password, list(keylist.keys()))

if keyboard_process is None:
    print("Failed to initialize keyboard listener. Exiting.")
    sys.exit(1)
    
present_dynamic_menu(keylist, audio_files)

# Send keylist to the subprocess
keyboard_process.stdin.write(json.dumps(list(keylist.keys())) + '\n')
keyboard_process.stdin.flush()

# Give subprocess a moment to initialize
time.sleep(0.5)

try:
    while True:
        # Check if subprocess is still running
        if keyboard_process.poll() is not None:
            stderr_output = keyboard_process.stderr.read()
            print(f"Keyboard listener process exited. Error: {stderr_output}")
            break
        
        # Read from keyboard listener process with timeout-like behavior
        try:
            key_input = keyboard_process.stdout.readline().strip()
        except:
            break
        
        if not key_input:
            break
            
        if key_input == 'DELETE':
            # Stop all channels
            for ch in channels:
                ch.stop()
            playing_keys.clear()  # Clear tracking when all sounds are stopped
            print("All sounds stopped!")
            time.sleep(0.3)
            os.system('clear' if os.name != 'nt' else 'cls')
            present_dynamic_menu(keylist, audio_files)
        elif key_input == 'TAB':
            # Fade out the most recently played channel
            if last_channel_used and last_channel_used.get_busy():
                fade_out_channel(last_channel_used)
                print("Fading out track...")
                time.sleep(0.3)
                os.system('clear' if os.name != 'nt' else 'cls')
                present_dynamic_menu(keylist, audio_files)
        elif key_input == 'DOWN':
            # Move to next page
            if current_page < total_pages - 1:
                current_page += 1
                page_offset = current_page * 36
                os.system('clear' if os.name != 'nt' else 'cls')
                present_dynamic_menu(keylist, audio_files)
        elif key_input == 'UP':
            # Move to previous page
            if current_page > 0:
                current_page -= 1
                page_offset = current_page * 36
                os.system('clear' if os.name != 'nt' else 'cls')
                present_dynamic_menu(keylist, audio_files)
        elif key_input == 'ESC':
            time.sleep(0.01)
            os.system('clear' if os.name != 'nt' else 'cls')
            print('Exiting...')
            time.sleep(0.4)
            os.system('clear' if os.name != 'nt' else 'cls')
            break
        elif key_input in keylist:
            # Only play if the key is not already playing
            if not is_key_playing(key_input):
                pressed_it(key_input, audio_files)

except KeyboardInterrupt:
    print('Exiting...')
finally:
    if keyboard_process:
        keyboard_process.terminate()
        try:
            keyboard_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            keyboard_process.kill()
        keyboard_process.wait(timeout=2)
    
    # Flush stdin to clear any buffered keypresses
    try:
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except:
        pass
