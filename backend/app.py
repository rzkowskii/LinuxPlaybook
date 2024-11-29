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
    'Documents': 'directory',
    'Downloads': 'directory',
    'Pictures': 'directory',
    'Desktop': 'directory',
    'file1.txt': 'file',
    'file2.txt': 'file',
    'example.pdf': 'file'
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
    'mock_files': MOCK_FILES.copy()
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
    
    # Split command into parts
    parts = command.split()
    base_command = parts[0] if parts else ''
    args = parts[1:] if len(parts) > 1 else []
    
    # Handle basic commands
    if command == "whoami":
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
    elif command == "ls":
        files = ' '.join(sorted(command_state['mock_files'].keys()))
        return jsonify({
            "output": files,
            "simulated": True,
            "success": True
        })
    elif command == "pwd":
        return jsonify({
            "output": "/home/john",
            "simulated": True,
            "success": True
        })
    elif command == "history":
        return jsonify({
            "output": "   1  ls -l\n   2  cd /etc\n   3  cat passwd\n   4  history",
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
    elif command.startswith("cat "):
        filename = command[4:]
        if filename == "/etc/passwd":
            return jsonify({
                "output": "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n...",
                "simulated": True,
                "success": True
            })
    elif command.startswith("head "):
        filename = command[5:]
        if filename == "/var/log/syslog":
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
    elif command.startswith("wc "):
        filename = command[3:]
        if filename == "/etc/hosts":
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
    elif base_command == "mkdir" and len(args) == 1:
        dirname = args[0]
        command_state['mock_files'][dirname] = 'directory'
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
            command_state['mock_files'][dst] = command_state['mock_files'][src]
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
