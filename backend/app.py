from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
from datetime import datetime
import json

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
    '.config': {'type': 'directory', 'size': 4096, 'perms': 'drwxr-xr-x', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 09:00'}
}

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
    'passwd_stage': 0,  # 0: start, 1: current password, 2: new password, 3: confirm password
    'current_password': None,
    'new_password': None,
    'mock_files': MOCK_FILES.copy(),
    'last_ls_command': None,
    'last_command': None,
    'command_history': [
        'ls -l',
        'cd /etc',
        'cat passwd',
        'history',
        'ping google.com',
        'wc -l /etc/passwd',
        'date +%R',
        'file /etc/passwd',
        'head -n 3 /etc/passwd',
        'tail -n 3 /etc/passwd'
    ]
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
    
    # Handle history expansion
    if command == "!!":
        if command_state['last_command']:
            command = command_state['last_command']
            parts = command.split()
            base_command = parts[0]
            args = parts[1:] if len(parts) > 1 else []
        else:
            return jsonify({
                "output": "No commands in history",
                "simulated": True
            })
    
    # Handle ls commands
    if base_command == "ls":
        if len(args) == 0:
            # Simple ls
            files = ' '.join(sorted(name for name in command_state['mock_files'].keys() if not name.startswith('.')))
            return jsonify({
                "output": files,
                "simulated": True,
                "success": True
            })
        elif "-a" in args:
            # ls -a (show hidden files)
            files = ' '.join(sorted(command_state['mock_files'].keys()))
            return jsonify({
                "output": files,
                "simulated": True,
                "success": True
            })
        elif "-l" in args:
            # ls -l (long format)
            output = "total 64\n"
            for name, info in sorted(command_state['mock_files'].items()):
                if not name.startswith('.'):  # Skip hidden files unless -a is present
                    output += f"{info['perms']} 1 {info['owner']} {info['group']} {info['size']} {info['date']} {name}\n"
            return jsonify({
                "output": output.rstrip(),
                "simulated": True,
                "success": True
            })
        elif len(args) == 1 and not args[0].startswith('-'):
            # ls with directory path
            if args[0] == "/etc":
                return jsonify({
                    "output": "apache2   hostname   passwd   ssh   ...",
                    "simulated": True,
                    "success": True
                })
    
    # Handle other commands
    elif command.startswith("date "):
        if command == "date '+%H:%M'" or command == "date +%R":
            return jsonify({
                "output": datetime.now().strftime("%H:%M"),
                "simulated": True,
                "success": True
            })
        elif command == "date '+%m/%d/%Y'":
            return jsonify({
                "output": datetime.now().strftime("%m/%d/%Y"),
                "simulated": True,
                "success": True
            })
    elif command == "whoami":
        return jsonify({
            "output": "john",
            "simulated": False,
            "success": True
        })
    elif command == "date":
        return jsonify({
            "output": datetime.now().strftime("%c"),
            "simulated": False,
            "success": True
        })
    elif command == "pwd":
        return jsonify({
            "output": "/home/john",
            "simulated": True,
            "success": True
        })
    elif command.startswith("file "):
        filename = command[5:]
        if filename == "/bin/ls":
            return jsonify({
                "output": "/bin/ls: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), dynamically linked...",
                "simulated": True,
                "success": True
            })
        elif filename == "/etc/passwd":
            return jsonify({
                "output": "/etc/passwd: ASCII text",
                "simulated": True,
                "success": True
            })
        elif filename == "/bin/passwd":
            return jsonify({
                "output": "/bin/passwd: setuid ELF 64-bit LSB shared object, x86-64, version 1 (SYSV)...",
                "simulated": True,
                "success": True
            })
        elif filename == "/home":
            return jsonify({
                "output": "/home: directory",
                "simulated": True,
                "success": True
            })
    elif command.startswith("cat "):
        files = command[4:].split()
        if len(files) > 1:
            return jsonify({
                "output": "... (contents of file1.txt)\n... (contents of file2.txt)",
                "simulated": True,
                "success": True
            })
        elif files[0] == "/etc/passwd":
            return jsonify({
                "output": "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n...",
                "simulated": True,
                "success": True
            })
    elif command.startswith("head "):
        if "-n 3" in command:
            if "/usr/share/dict/words" in command and "/usr/share/dict/linux.words" in command:
                return jsonify({
                    "output": "==> /usr/share/dict/words <==\nA\na\naa\n\n==> /usr/share/dict/linux.words <==\n4th\nAbbas\nabbey",
                    "simulated": True,
                    "success": True
                })
            elif "/etc/passwd" in command:
                return jsonify({
                    "output": "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\nbin:x:2:2:bin:/bin:/usr/sbin/nologin",
                    "simulated": True,
                    "success": True
                })
        elif command.startswith("head /var/log/syslog"):
            return jsonify({
                "output": "Oct 18 14:55:03 hostname systemd[1]: Started Session 1 of user john.\nOct 18 14:55:05 hostname sshd[1234]: Accepted password for john from 192.168.1.2 port 54321\n...",
                "simulated": True,
                "success": True
            })
    elif command.startswith("tail "):
        if "-n 3" in command and "/etc/passwd" in command:
            return jsonify({
                "output": "sshd:x:74:74:Privilege-separated SSH:/var/empty/sshd:/sbin/nologin\njohn:x:1001:1001:John Doe,,,:/home/john:/bin/bash",
                "simulated": True,
                "success": True
            })
        elif command == "tail /var/log/syslog":
            return jsonify({
                "output": "... (last 10 lines of syslog)",
                "simulated": True,
                "success": True
            })
    elif command.startswith("wc "):
        if command == "wc /etc/passwd":
            return jsonify({
                "output": "  45   63 1935 /etc/passwd\nLines: 45\nWords: 63\nCharacters: 1935",
                "simulated": True,
                "success": True
            })
        elif command == "wc -l /etc/passwd /etc/group":
            return jsonify({
                "output": "  45 /etc/passwd\n  60 /etc/group\n 105 total",
                "simulated": True,
                "success": True
            })
        elif command == "wc -c /etc/group /etc/hosts":
            return jsonify({
                "output": " 2030 /etc/group\n  178 /etc/hosts\n 2208 total",
                "simulated": True,
                "success": True
            })
        elif command == "wc /etc/hosts":
            return jsonify({
                "output": "  12   22  178 /etc/hosts\nLines: 12\nWords: 22\nCharacters: 178",
                "simulated": True,
                "success": True
            })
    elif command.startswith("echo "):
        if "multi-line" in command:
            return jsonify({
                "output": "This is a multi-line command",
                "simulated": True,
                "success": True
            })
    elif ";" in command:
        # Handle multiple commands
        commands = command.split(";")
        output = []
        for cmd in commands:
            if cmd.strip() == "cd /var/log":
                output.append("Changes directory to /var/log")
            elif cmd.strip() == "ls":
                output.append("Lists files in /var/log")
            elif cmd.strip() == "pwd":
                output.append("Displays the current directory")
        return jsonify({
            "output": "\n".join(output),
            "simulated": True,
            "success": True
        })
    elif base_command == "mkdir" and len(args) == 1:
        dirname = args[0]
        command_state['mock_files'][dirname] = {
            'type': 'directory',
            'size': 4096,
            'perms': 'drwxr-xr-x',
            'owner': 'user',
            'group': 'user',
            'date': datetime.now().strftime("%b %d %H:%M")
        }
        return jsonify({
            "output": "",
            "simulated": True,
            "success": True
        })
    elif base_command == "rm":
        if len(args) == 1:
            filename = args[0]
            if filename in command_state['mock_files']:
                del command_state['mock_files'][filename]
            return jsonify({
                "output": "",
                "simulated": True,
                "success": True
            })
        elif len(args) == 2 and args[0] == "-r":
            dirname = args[1]
            if dirname in command_state['mock_files']:
                del command_state['mock_files'][dirname]
            return jsonify({
                "output": "",
                "simulated": True,
                "success": True
            })
    elif base_command == "cp" and len(args) == 2:
        src, dst = args
        if src in command_state['mock_files']:
            command_state['mock_files'][dst] = command_state['mock_files'][src].copy()
        return jsonify({
            "output": "",
            "simulated": True,
            "success": True
        })
    elif base_command == "mv" and len(args) == 2:
        src, dst = args
        if src in command_state['mock_files']:
            command_state['mock_files'][dst] = command_state['mock_files'][src]
            del command_state['mock_files'][src]
        return jsonify({
            "output": "",
            "simulated": True,
            "success": True
        })
    elif command == "passwd":
        command_state['passwd_stage'] = 1
        return jsonify({
            "output": "Changing password for user john.\nCurrent password:",
            "simulated": True,
            "prompt": "password"
        })
    elif command_state['passwd_stage'] > 0:
        # Handle password stages
        if command_state['passwd_stage'] == 1:
            command_state['current_password'] = command
            command_state['passwd_stage'] = 2
            return jsonify({
                "output": "New password:",
                "simulated": True,
                "prompt": "password"
            })
        elif command_state['passwd_stage'] == 2:
            command_state['new_password'] = command
            command_state['passwd_stage'] = 3
            return jsonify({
                "output": "Retype new password:",
                "simulated": True,
                "prompt": "password"
            })
        elif command_state['passwd_stage'] == 3:
            # Reset password state
            command_state['passwd_stage'] = 0
            command_state['current_password'] = None
            command_state['new_password'] = None
            return jsonify({
                "output": "passwd: all authentication tokens updated successfully.",
                "simulated": True,
                "success": True
            })
    
    # Default response for unknown commands
    return jsonify({
        "output": f"Command not recognized. Please try again.",
        "simulated": True
    })

@app.route('/api/levels', methods=['GET'])
def get_levels():
    """Return all levels"""
    return jsonify(load_levels())

@app.route('/api/flashcards', methods=['GET'])
def get_flashcards():
    """Return all flashcards"""
    return jsonify(get_all_flashcards())

@app.route('/api/flashcards/<int:id>', methods=['GET'])
def get_flashcard(id):
    """Return a specific flashcard"""
    flashcards = get_all_flashcards()
    flashcard = next((card for card in flashcards if card["id"] == id), None)
    if flashcard is None:
        return jsonify({"error": "Flashcard not found"}), 404
    return jsonify(flashcard)

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Return unique categories from flashcards"""
    flashcards = get_all_flashcards()
    categories = list(set(card["category"] for card in flashcards))
    return jsonify(categories)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
