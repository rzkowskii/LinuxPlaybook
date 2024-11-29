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

# Flashcards data
FLASHCARDS = [
    {
        "id": 1,
        "question": "What command displays the current user's username in the terminal?",
        "answer": "whoami",
        "example": "$ whoami\njohn",
        "category": "User Commands"
    },
    {
        "id": 2,
        "question": "How do you find the current date and time in the terminal?",
        "answer": "Use the date command.",
        "example": "$ date\nWed Oct 18 14:55:02 PDT 2023",
        "category": "System Information"
    },
    {
        "id": 3,
        "question": "What command allows the current user to change their password?",
        "answer": "passwd",
        "example": "$ passwd\nChanging password for user john.\nCurrent password:\nNew password:\nRetype new password:\npasswd: all authentication tokens updated successfully.",
        "category": "User Management"
    },
    {
        "id": 4,
        "question": "How do you list all files and directories in the current directory?",
        "answer": "ls",
        "example": "$ ls\nDocuments Downloads Pictures Desktop file1.txt file2.txt example.pdf",
        "category": "File System"
    },
    {
        "id": 5,
        "question": "What command shows the current working directory?",
        "answer": "pwd",
        "example": "$ pwd\n/home/john",
        "category": "File System"
    },
    {
        "id": 6,
        "question": "How do you create a new directory?",
        "answer": "mkdir",
        "example": "$ mkdir new_directory",
        "category": "File System"
    },
    {
        "id": 7,
        "question": "What command removes a file?",
        "answer": "rm",
        "example": "$ rm file.txt",
        "category": "File System"
    },
    {
        "id": 8,
        "question": "How do you remove a directory and its contents?",
        "answer": "rm -r",
        "example": "$ rm -r directory_name",
        "category": "File System"
    },
    {
        "id": 9,
        "question": "What command copies files or directories?",
        "answer": "cp",
        "example": "$ cp source.txt destination.txt",
        "category": "File System"
    },
    {
        "id": 10,
        "question": "How do you move or rename files and directories?",
        "answer": "mv",
        "example": "$ mv old_name.txt new_name.txt",
        "category": "File System"
    }
]

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
            "simulated": False
        })
    elif command == "date":
        return jsonify({
            "output": datetime.now().strftime("%c"),
            "simulated": False
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

@app.route('/api/flashcards', methods=['GET'])
def get_flashcards():
    """Return all flashcards"""
    return jsonify(FLASHCARDS)

@app.route('/api/flashcards/<int:id>', methods=['GET'])
def get_flashcard(id):
    """Return a specific flashcard"""
    flashcard = next((card for card in FLASHCARDS if card["id"] == id), None)
    if flashcard is None:
        return jsonify({"error": "Flashcard not found"}), 404
    return jsonify(flashcard)

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Return unique categories from flashcards"""
    categories = list(set(card["category"] for card in FLASHCARDS))
    return jsonify(categories)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
