import bpy, sys, time, os, subprocess, tempfile

def get_addon_preferences():
    addon = bpy.context.preferences.addons.get(__package__)
    return getattr(addon, "preferences", None)

_MACRO_COMMANDS = []
_pipe_connection = None

def get_pipe_path():
    """Get the correct pipe path based on platform."""
    if sys.platform == "win32":
        return "\\\\.\\pipe\\audacity_script"
    elif sys.platform == "darwin":
        return "/tmp/audacity_script"
    else:  # Linux
        return "/tmp/audacity_script"

def open_pipe():
    """Open connection to Audacity's Mod-Script pipe."""
    global _pipe_connection
    try:
        if sys.platform == "win32":
            import win32file, win32pipe
            handle = win32pipe.CreateNamedPipe(
                "\\\\.\\pipe\\audacity_script",
                win32pipe.PIPE_ACCESS_DUPLEX,
                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                1, 65536, 65536,
                0,
                None
            )
            _pipe_connection = handle
        else:
            # For Unix-like systems, use socket or FIFO
            pipe_path = get_pipe_path()
            if os.path.exists(pipe_path):
                _pipe_connection = open(pipe_path, 'w')
            else:
                _pipe_connection = None
        return _pipe_connection is not None
    except Exception as e:
        print(f"Error opening pipe: {e}")
        _pipe_connection = None
        return False

def close_pipe():
    """Close the pipe connection."""
    global _pipe_connection
    if _pipe_connection:
        try:
            if sys.platform == "win32":
                import win32file
                win32file.CloseHandle(_pipe_connection)
            else:
                _pipe_connection.close()
        except Exception:
            pass
        _pipe_connection = None

def send_via_pipe(command):
    """Send command to Audacity via Mod-Script pipe."""
    global _pipe_connection
    try:
        # Try to open pipe if not already open
        if _pipe_connection is None:
            if sys.platform == "win32":
                # Windows named pipe
                import win32file
                try:
                    handle = win32file.CreateFile(
                        "\\\\.\\pipe\\audacity_script",
                        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                        0, None,
                        win32file.OPEN_EXISTING,
                        0, None
                    )
                    _pipe_connection = handle
                except Exception as e:
                    print(f"Cannot connect to pipe: {e}")
                    return False
            else:
                # Unix - write to pipe file
                pipe_path = get_pipe_path()
                if os.path.exists(pipe_path):
                    _pipe_connection = open(pipe_path, 'w')
                else:
                    return False
        
        if sys.platform == "win32":
            import win32file
            win32file.WriteFile(_pipe_connection, (command + "\n").encode())
        else:
            _pipe_connection.write(command + "\n")
            _pipe_connection.flush()
        
        return True
    except Exception as e:
        print(f"Error sending command: {e}")
        _pipe_connection = None
        return False

def return_audacity_pipe():
    return None, None, None

def check_set_pipe(launch=True):
    winman = bpy.data.window_managers[0]
    app_path = get_addon_preferences().audacity_executable
    is_valid = os.path.isfile(app_path)
    
    # Also check if pipe is available (Audacity is running with scripting enabled)
    pipe_available = False
    if sys.platform == "win32":
        import win32file
        try:
            handle = win32file.CreateFile(
                "\\\\.\\pipe\\audacity_script",
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0, None,
                win32file.OPEN_EXISTING,
                0, None
            )
            win32file.CloseHandle(handle)
            pipe_available = True
        except Exception:
            pipe_available = False
    else:
        pipe_path = get_pipe_path()
        pipe_available = os.path.exists(pipe_path)
    
    winman.audacity_tools_pipe_available = is_valid and pipe_available
    return winman.audacity_tools_pipe_available

def check_pipe():
    winman = bpy.data.window_managers[0]
    app_path = get_addon_preferences().audacity_executable
    is_valid = os.path.isfile(app_path)
    
    # Also check if pipe is available (Audacity is running with scripting enabled)
    pipe_available = False
    if sys.platform == "win32":
        import win32file
        try:
            handle = win32file.CreateFile(
                "\\\\.\\pipe\\audacity_script",
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0, None,
                win32file.OPEN_EXISTING,
                0, None
            )
            win32file.CloseHandle(handle)
            pipe_available = True
        except Exception:
            pipe_available = False
    else:
        pipe_path = get_pipe_path()
        pipe_available = os.path.exists(pipe_path)
    
    winman.audacity_tools_pipe_available = is_valid and pipe_available
    return winman.audacity_tools_pipe_available

def launch_audacity():
    app_path = get_addon_preferences().audacity_executable
    if os.path.isfile(app_path):
        if sys.platform == "win32":
            os.startfile(app_path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", app_path])
        else:
            subprocess.Popen([app_path])
        return True
    else:
        return False

def send_command(command):
    global _MACRO_COMMANDS
    _MACRO_COMMANDS.append(command)

def get_response():
    return ""

def simulate_key(key):
    import subprocess
    try:
        subprocess.Popen(['xdotool', 'search', '--class', 'Audacity', 'windowactivate', '--sync', 'key', key],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def do_command(command):
    """Send command to Audacity via Mod-Script pipe."""
    print("Sending command: >>> " + command)
    
    # First try to send via pipe
    if send_via_pipe(command):
        return ""
    
    # Fallback to key simulation for basic commands
    if "Play" in command or "Stop" in command:
        simulate_key("space")
    elif "Record" in command:
        simulate_key("r")
    
    send_command(command)
    return ""

def forward_file(filepath):
    """Send file to Audacity - opens new instance."""
    app_path = get_addon_preferences().audacity_executable
    if os.path.isfile(app_path):
        import subprocess
        subprocess.Popen([app_path, filepath])
    else:
        print(f"Audacity not found at {app_path}")

def import_to_existing_audacity(filepath):
    """Import file to existing Audacity session via pipe."""
    filename = '"' + filepath + '"'
    command = f'Import2: Filename={filename}'
    return do_command(command)
