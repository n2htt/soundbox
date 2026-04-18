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

def create_keylist(audio_files):
    """Create a dictionary mapping keys to audio filenames."""
    keylist = {}
    for i, filename in enumerate(audio_files):
        if i < 10:
            key = str(i)
        else:
            key = chr(ord('a') + (i - 10))
        keylist[key] = filename
    return keylist

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

def present_dynamic_menu(keylist):
    """Present the menu with dynamic key assignments."""
    global first_menu
    os.system('clear' if os.name != 'nt' else 'cls')
    if first_menu:
        print("Welcome to the Soundbox!")
        first_menu = False
    for key, filename in keylist.items():
        print(f"Press '{key}' to play sound {os.path.basename(filename)}")
    print("Press 'DELETE' to interrupt playback")
    print("Press 'ESC' to exit")

def pressed_it(kn):
    global interrupt_playback
    time.sleep(0.01)
    os.system('clear' if os.name != 'nt' else 'cls')
    print(f"\nPlaying file {kn}: ")
    pygame.mixer.music.load(keylist[kn])
    pygame.mixer.music.play()

    interrupt_playback = False
    
    # Monitor playback while checking for interrupt keys
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
        
        # Non-blocking check for keyboard input during playback
        try:
            # Use select to check if data is available without blocking
            ready, _, _ = select.select([keyboard_process.stdout], [], [], 0.05)
            if ready:
                key_input = keyboard_process.stdout.readline().strip()
                if key_input == 'DELETE':
                    pygame.mixer.music.stop()
                    print("Playback interrupted!")
                    interrupt_playback = True
                    break
                elif key_input == 'ESC':
                    pygame.mixer.music.stop()
                    interrupt_playback = True
                    return 'EXIT'
                elif key_input in keylist:
                    # Queue this key for later processing
                    pygame.mixer.music.stop()
                    interrupt_playback = True
                    return key_input
        except:
            pass
    
    if not interrupt_playback:
        print("Playback finished!")
    
    time.sleep(0.3)
    os.system('clear' if os.name != 'nt' else 'cls')
    present_dynamic_menu(keylist)

pygame.mixer.init()
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

keylist = create_keylist(audio_files)

password = get_password()

# Start keyboard listener with elevated privilege 
keyboard_process = start_keyboard_listener(password, list(keylist.keys()))

if keyboard_process is None:
    print("Failed to initialize keyboard listener. Exiting.")
    sys.exit(1)
    
present_dynamic_menu(keylist)

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
            
        if key_input == 'ESC':
            time.sleep(0.01)
            os.system('clear' if os.name != 'nt' else 'cls')
            print('Exiting...')
            time.sleep(0.4)
            os.system('clear' if os.name != 'nt' else 'cls')
            break

        if key_input in keylist:
            result = pressed_it(key_input)
            # Handle if a key was pressed during playback or EXIT signal
            if result == 'EXIT':
                time.sleep(0.01)
                os.system('clear' if os.name != 'nt' else 'cls')
                print('Exiting...')
                time.sleep(0.4)
                os.system('clear' if os.name != 'nt' else 'cls')
                break
            elif result in keylist:
                # Immediately play the key that was pressed during playback
                result = pressed_it(result)

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
