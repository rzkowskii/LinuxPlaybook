from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
from datetime import datetime
import json
import glob
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Mock file system data
MOCK_FILES = {
    'Documents': {'type': 'directory', 'size': 4096, 'perms': 'drwxr-xr-x', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 10:20'},
    'Downloads': {'type': 'directory', 'size': 4096, 'perms': 'drwxr-xr-x', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 10:15'},
    'Pictures': {'type': 'directory', 'size': 4096, 'perms': 'drwxr-xr-x', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 10:10'},
    'Desktop': {'type': 'directory', 'size': 4096, 'perms': 'drwxr-xr-x', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 10:05'},
    'file1.txt': {'type': 'file', 'size': 512, 'perms': '-rw-r--r--', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 09:20'},
    'file2.txt': {'type': 'file', 'size': 1024, 'perms': '-rw-r--r--', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 09:15'},
    'example.pdf': {'type': 'file', 'size': 2048, 'perms': '-rw-r--r--', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 09:10'},
    '.hidden1': {'type': 'file', 'size': 128, 'perms': '-rw-r--r--', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 09:05'},
    '.config': {'type': 'directory', 'size': 4096, 'perms': 'drwxr-xr-x', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 09:00'},
    'report_1.pdf': {'type': 'file', 'size': 1024, 'perms': '-rw-r--r--', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 11:00'},
    'report_2.pdf': {'type': 'file', 'size': 1024, 'perms': '-rw-r--r--', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 11:05'},
    'report_3.pdf': {'type': 'file', 'size': 1024, 'perms': '-rw-r--r--', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 11:10'},
    'symlink.txt': {'type': 'link', 'size': 20, 'perms': 'lrwxrwxrwx', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 15:30', 'target': '/home/user/original_file.txt'}
}

# Mock environment variables
MOCK_ENV = {
    'USER': 'user',
    'HOME': '/home/user',
    'PATH': '/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin',
    'SHELL': '/bin/bash',
    'PWD': '/home/user',
    'TERM': 'xterm-256color'
}

def match_pattern(pattern, files):
    """Match files against a shell pattern"""
    if '[[:digit:]]' in pattern:
        pattern = pattern.replace('[[:digit:]]', '[0-9]')
    pattern = pattern.replace('*', '.*').replace('?', '.')
    regex = re.compile(f'^{pattern}$')
    return [f for f in files if regex.match(f)]

def expand_brace(pattern):
    """Handle brace expansion like {1..3}"""
    if '{' not in pattern or '}' not in pattern:
        return [pattern]
    
    match = re.search(r'\{(\d+)\.\.(\d+)\}', pattern)
    if match:
        start, end = map(int, match.groups())
        prefix = pattern[:match.start()]
        suffix = pattern[match.end():]
        return [f"{prefix}{i}{suffix}" for i in range(start, end + 1)]
    return [pattern]

def load_levels():
    """Load all level files from the levels directory"""
    levels = []
    levels_dir = os.path.join(os.path.dirname(__file__), 'levels')
    for filename in os.listdir(levels_dir):
        if filename.endswith('.json'):
            with open(os.path.join(levels_dir, filename), 'r') as f:
                level = json.load(f)
                levels.append(level)
    return sorted(levels, key=lambda x: x['order'])

def get_all_flashcards():
    """Get all flashcards from all levels"""
    levels = load_levels()
    flashcards = []
    for level in levels:
        flashcards.extend(level['flashcards'])
    return flashcards

# Command state
command_state = {
    'passwd_stage': 0,
    'current_password': None,
    'new_password': None,
    'mock_files': MOCK_FILES.copy(),
    'current_dir': '/home/user',
    'last_ls_command': None,
    'last_command': None,
    'command_history': [
        'ls -l',
        'cd /etc',
        'cat passwd',
        'history',
        'ping google.com'
    ],
    'env_vars': MOCK_ENV.copy()
}

@app.route('/api/execute', methods=['POST'])
def execute_command():
    """Handle command execution or simulation"""
    data = request.get_json()
    command = data.get('command', '').strip()
    
    # Handle empty commands
    if not command:
        return jsonify({
            "output": "",
            "simulated": True
        })
    
    # Store last command for !! history expansion
    if command != "!!":
        command_state['last_command'] = command
    
    # Split command into parts
    parts = command.split()
    base_command = parts[0] if parts else ''
    args = parts[1:] if len(parts) > 1 else []
    
    # Handle pattern matching commands
    if base_command == "ls" and any('*' in arg or '?' in arg or '[' in arg for arg in args):
        matched_files = []
        for pattern in args:
            matched = match_pattern(pattern, command_state['mock_files'].keys())
            matched_files.extend(matched)
        return jsonify({
            "output": ' '.join(sorted(matched_files)),
            "simulated": True,
            "success": True
        })
    
    # Handle brace expansion
    elif '{' in command and '}' in command:
        expanded = expand_brace(command)
        return jsonify({
            "output": ' '.join(expanded),
            "simulated": True,
            "success": True
        })
    
    # Handle variable operations
    elif base_command == "export":
        if len(args) == 1 and '=' in args[0]:
            var_name, var_value = args[0].split('=', 1)
            command_state['env_vars'][var_name] = var_value.strip('"')
            return jsonify({
                "output": "",
                "simulated": True,
                "success": True
            })
    
    elif base_command == "echo":
        if len(args) == 1:
            if args[0].startswith('$'):
                # Variable expansion
                var_name = args[0][1:].strip('{}')
                if var_name in command_state['env_vars']:
                    return jsonify({
                        "output": command_state['env_vars'][var_name],
                        "simulated": True,
                        "success": True
                    })
            elif args[0].startswith('~'):
                # Tilde expansion
                user = args[0][1:] or 'user'
                home_dir = '/root' if user == 'root' else f'/home/{user}'
                return jsonify({
                    "output": home_dir,
                    "simulated": True,
                    "success": True
                })
            elif args[0].startswith('$(') and args[0].endswith(')'):
                # Command substitution
                inner_command = args[0][2:-1]
                if inner_command == 'date +%A':
                    return jsonify({
                        "output": datetime.now().strftime("%A"),
                        "simulated": True,
                        "success": True
                    })
    
    # Handle other commands (previous implementation remains unchanged)
    # ... (rest of the execute_command function remains the same)

    return jsonify({
        "output": f"Command not recognized. Please try again.",
        "simulated": True
    })

# ... (rest of the file remains the same)
