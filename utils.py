import bpy, sys, os, subprocess

def get_addon_preferences():
    addon = bpy.context.preferences.addons.get(__package__)
    return getattr(addon, "preferences", None)

_MACRO_COMMANDS = []

def check_set_pipe():
    winman = bpy.data.window_managers[0]
    app_path = get_addon_preferences().audacity_executable
    is_valid = os.path.isfile(app_path)
    winman.audacity_tools_pipe_available = is_valid
    return is_valid

def check_pipe():
    winman = bpy.data.window_managers[0]
    app_path = get_addon_preferences().audacity_executable
    is_valid = os.path.isfile(app_path)
    winman.audacity_tools_pipe_available = is_valid
    return is_valid

def send_command(command):
    global _MACRO_COMMANDS
    _MACRO_COMMANDS.append(command)

def simulate_key(key):
    import subprocess
    try:
        subprocess.Popen(['xdotool', 'search', '--class', 'Audacity', 'windowactivate', '--sync', 'key', key],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def do_command(command):
    print("Buffered: >>> " + command)
    if "Play" in command or "Stop" in command:
        simulate_key("space")
    elif "Record" in command:
        simulate_key("r")
        
    send_command(command)
    return ""

def forward_file(filepath):
    app_path = get_addon_preferences().audacity_executable
    if os.path.isfile(app_path):
        import subprocess
        subprocess.Popen([app_path, filepath])
    else:
        print(f"Audacity not found at {app_path}")
