from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
from datetime import datetime
import json
import glob
import re
import shlex
import socket

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Mock file system data
MOCK_FILES = {
    'Documents': {'type': 'directory', 'size': 4096, 'perms': 'drwxr-xr-x', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 10:20', 'inode': 1001},
    'Downloads': {'type': 'directory', 'size': 4096, 'perms': 'drwxr-xr-x', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 10:15', 'inode': 1002},
    'Pictures': {'type': 'directory', 'size': 4096, 'perms': 'drwxr-xr-x', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 10:10', 'inode': 1003},
    'Desktop': {'type': 'directory', 'size': 4096, 'perms': 'drwxr-xr-x', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 10:05', 'inode': 1004},
    'file1.txt': {'type': 'file', 'size': 512, 'perms': '-rw-r--r--', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 09:20', 'inode': 1005},
    'file2.txt': {'type': 'file', 'size': 1024, 'perms': '-rw-r--r--', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 09:15', 'inode': 1006},
    'example.pdf': {'type': 'file', 'size': 2048, 'perms': '-rw-r--r--', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 09:10', 'inode': 1007},
    '.hidden1': {'type': 'file', 'size': 128, 'perms': '-rw-r--r--', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 09:05', 'inode': 1008},
    '.config': {'type': 'directory', 'size': 4096, 'perms': 'drwxr-xr-x', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 09:00', 'inode': 1009},
    'report_1.pdf': {'type': 'file', 'size': 1024, 'perms': '-rw-r--r--', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 11:00', 'inode': 1010},
    'report_2.pdf': {'type': 'file', 'size': 1024, 'perms': '-rw-r--r--', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 11:05', 'inode': 1011},
    'report_3.pdf': {'type': 'file', 'size': 1024, 'perms': '-rw-r--r--', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 11:10', 'inode': 1012},
    'symlink.txt': {'type': 'link', 'size': 20, 'perms': 'lrwxrwxrwx', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 15:30', 'target': '/home/user/original_file.txt', 'inode': 1013},
    'broken_symlink.txt': {'type': 'link', 'size': 20, 'perms': 'lrwxrwxrwx', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 16:00', 'target': '/nonexistent/file.txt', 'inode': 1014},
    'hardlink.txt': {'type': 'file', 'size': 512, 'perms': '-rw-r--r--', 'owner': 'user', 'group': 'user', 'date': 'Oct 18 09:20', 'inode': 1005}  # Same inode as file1.txt
}

# Mock environment variables
MOCK_ENV = {
    'USER': 'user',
    'HOME': '/home/user',
    'PATH': '/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin',
    'SHELL': '/bin/bash',
    'PWD': '/home/user',
    'TERM': 'xterm-256color',
    'OLDPWD': '/var/log',  # For cd - command
    'USERNAME': 'user'
}

# Mock system information
MOCK_SYSTEM = {
    'hostname': 'mycomputer.example.com',
    'short_hostname': 'mycomputer',
    'domain': 'example.com'
}

def get_home_dir(username=None):
    """Get home directory for a user"""
    if username == 'root':
        return '/root'
    elif username:
        return f'/home/{username}'
    return MOCK_ENV['HOME']

def list_directory_recursive(path='.'):
    """Generate recursive directory listing"""
    output = []
    output.append(f"{path}:")
    files = [name for name in command_state['mock_files'].keys() if not name.startswith('.')]
    output.append(' '.join(sorted(files)))
    
    # Add subdirectories
    for name, info in command_state['mock_files'].items():
        if info['type'] == 'directory' and not name.startswith('.'):
            output.append(f"\n./{name}:")
            output.append("example_file1.txt  example_file2.txt")
    
    return '\n'.join(output)

def match_pattern(pattern, files):
    """Match files against a shell pattern"""
    if '[[:digit:]]' in pattern:
        pattern = pattern.replace('[[:digit:]]', '[0-9]')
    elif '[[:alnum:]]' in pattern:
        pattern = pattern.replace('[[:alnum:]]', '[a-zA-Z0-9]')
    elif '[[:punct:]]' in pattern:
        pattern = pattern.replace('[[:punct:]]', '[!a-zA-Z0-9]')
    elif pattern.startswith('[!'):
        # Handle negated character classes
        neg_chars = pattern[2:pattern.index(']')]
        pattern = f'[^{neg_chars}]' + pattern[pattern.index(']')+1:]
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
    'previous_dir': '/var/log',  # For cd - command
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
    try:
        parts = shlex.split(command)  # Handles quotes properly
    except ValueError:
        # Handle unclosed quotes
        return jsonify({
            "output": "Syntax error: Unclosed quote",
            "simulated": True
        })
    
    base_command = parts[0] if parts else ''
    args = parts[1:] if len(parts) > 1 else []
    
    # Handle basic commands
    if command == "whoami":
        return jsonify({
            "output": "john",
            "simulated": True,
            "success": True
        })
    elif command == "date":
        return jsonify({
            "output": datetime.now().strftime("%c"),
            "simulated": True,
            "success": True
        })
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
    
    # Handle hostname command
    elif base_command == "hostname":
        if "-s" in args:
            return jsonify({
                "output": MOCK_SYSTEM['short_hostname'],
                "simulated": True,
                "success": True
            })
        elif "-f" in args:
            return jsonify({
                "output": MOCK_SYSTEM['hostname'],
                "simulated": True,
                "success": True
            })
        elif "-d" in args:
            return jsonify({
                "output": MOCK_SYSTEM['domain'],
                "simulated": True,
                "success": True
            })
        else:
            return jsonify({
                "output": MOCK_SYSTEM['hostname'],
                "simulated": True,
                "success": True
            })
    
    # Handle touch command with timestamp update
    elif base_command == "touch":
        if len(args) == 1:
            filename = args[0]
            if filename in command_state['mock_files']:
                command_state['mock_files'][filename]['date'] = datetime.now().strftime("%b %d %H:%M")
            else:
                command_state['mock_files'][filename] = {
                    'type': 'file',
                    'size': 0,
                    'perms': '-rw-r--r--',
                    'owner': 'user',
                    'group': 'user',
                    'date': datetime.now().strftime("%b %d %H:%M"),
                    'inode': max(info['inode'] for info in command_state['mock_files'].values()) + 1
                }
            return jsonify({
                "output": "",
                "simulated": True,
                "success": True
            })
    
    # Handle ln command for hard and symbolic links
    elif base_command == "ln":
        if len(args) >= 2:
            symbolic = "-s" in args
            if symbolic:
                args.remove("-s")
            source, target = args[-2:]
            if symbolic:
                command_state['mock_files'][target] = {
                    'type': 'link',
                    'size': len(source),
                    'perms': 'lrwxrwxrwx',
                    'owner': 'user',
                    'group': 'user',
                    'date': datetime.now().strftime("%b %d %H:%M"),
                    'target': source,
                    'inode': max(info['inode'] for info in command_state['mock_files'].values()) + 1
                }
            else:
                # Hard link shares the same inode
                if source in command_state['mock_files']:
                    command_state['mock_files'][target] = command_state['mock_files'][source].copy()
            return jsonify({
                "output": "",
                "simulated": True,
                "success": True
            })
    
    # Handle mv command with verbose output
    elif base_command == "mv":
        verbose = "-v" in args
        if verbose:
            args.remove("-v")
        if len(args) == 2:
            source, target = args
            if source in command_state['mock_files']:
                command_state['mock_files'][target] = command_state['mock_files'][source]
                del command_state['mock_files'][source]
                if verbose:
                    return jsonify({
                        "output": f"renamed '{source}' -> '{target}'",
                        "simulated": True,
                        "success": True
                    })
            return jsonify({
                "output": "",
                "simulated": True,
                "success": True
            })
    
    # Handle man command simulation
    elif base_command == "man":
        if len(args) == 1:
            return jsonify({
                "output": "Manual page viewer\nUse Spacebar or PageDown to scroll forward\nUse 'b' or PageUp to scroll backward\nUse 'q' to quit",
                "simulated": True,
                "success": True
            })
    
    # Handle cd commands
    elif base_command == "cd":
        old_dir = command_state['current_dir']
        if len(args) == 0 or args[0] == "~":
            command_state['current_dir'] = get_home_dir()
        elif args[0] == "-":
            command_state['current_dir'] = command_state['previous_dir']
            command_state['previous_dir'] = old_dir
            return jsonify({
                "output": command_state['current_dir'],
                "simulated": True,
                "success": True
            })
        elif args[0] == "..":
            command_state['current_dir'] = os.path.dirname(command_state['current_dir'])
        elif args[0] == ".":
            pass  # Stay in current directory
        elif args[0].startswith("~"):
            username = args[0][1:] or None
            command_state['current_dir'] = get_home_dir(username)
        elif args[0] == "-P" and len(args) > 1:
            # Handle cd -P for resolving symlinks
            path = args[1]
            if path in command_state['mock_files'] and command_state['mock_files'][path]['type'] == 'link':
                command_state['current_dir'] = command_state['mock_files'][path]['target']
            else:
                command_state['current_dir'] = path
        else:
            command_state['current_dir'] = args[0]
        command_state['previous_dir'] = old_dir
        return jsonify({
            "output": "",
            "simulated": True,
            "success": True
        })
    
    # Handle ls commands
    elif base_command == "ls":
        if "-i" in args:
            # Show inode numbers
            output = []
            for name, info in sorted(command_state['mock_files'].items()):
                if not name.startswith('.'):  # Skip hidden files unless -a is present
                    output.append(f"{info['inode']} {name}")
            return jsonify({
                "output": '\n'.join(output),
                "simulated": True,
                "success": True
            })
        elif "-R" in args:
            # Recursive listing
            output = list_directory_recursive()
            return jsonify({
                "output": output,
                "simulated": True,
                "success": True
            })
        elif any('[' in arg for arg in args):
            # Pattern matching
            matched_files = []
            for pattern in args:
                if '[' in pattern:
                    matched = match_pattern(pattern, command_state['mock_files'].keys())
                    matched_files.extend(matched)
            return jsonify({
                "output": ' '.join(sorted(matched_files)),
                "simulated": True,
                "success": True
            })
        elif len(args) == 0:
            # Simple ls
            files = ' '.join(sorted(name for name in command_state['mock_files'].keys() if not name.startswith('.')))
            return jsonify({
                "output": files,
                "simulated": True,
                "success": True
            })
        elif "-a" in args:
            # Show hidden files
            files = ' '.join(sorted(command_state['mock_files'].keys()))
            return jsonify({
                "output": files,
                "simulated": True,
                "success": True
            })
        elif "-l" in args:
            # Long format listing
            output = "total 64\n"
            for name, info in sorted(command_state['mock_files'].items()):
                if not name.startswith('.'):  # Skip hidden files unless -a is present
                    output += f"{info['perms']} 1 {info['owner']} {info['group']} {info['size']} {info['date']} {name}"
                    if info['type'] == 'link':
                        output += f" -> {info['target']}"
                    output += "\n"
            return jsonify({
                "output": output.rstrip(),
                "simulated": True,
                "success": True
            })
    
    # Handle echo commands
    elif base_command == "echo":
        if len(args) == 1:
            arg = args[0]
            if arg.startswith('\\'):
                # Handle escaped characters
                return jsonify({
                    "output": arg[1:],
                    "simulated": True,
                    "success": True
                })
            elif arg.startswith('$'):
                # Variable expansion
                var_name = arg[1:].strip('{}')
                if var_name in command_state['env_vars']:
                    return jsonify({
                        "output": command_state['env_vars'][var_name],
                        "simulated": True,
                        "success": True
                    })
            elif arg.startswith('~'):
                # Tilde expansion
                user = arg[1:] or 'user'
                if user == 'user' or user == 'root':
                    home_dir = '/root' if user == 'root' else f'/home/{user}'
                    return jsonify({
                        "output": home_dir,
                        "simulated": True,
                        "success": True
                    })
                else:
                    # Return unchanged for nonexistent users
                    return jsonify({
                        "output": arg,
                        "simulated": True,
                        "success": True
                    })
            elif '{' in arg and '}' in arg:
                # Handle brace expansion
                expanded = expand_brace(arg)
                return jsonify({
                    "output": ' '.join(expanded),
                    "simulated": True,
                    "success": True
                })
            else:
                # Regular echo
                return jsonify({
                    "output": arg,
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
