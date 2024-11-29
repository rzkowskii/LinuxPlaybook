from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

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
        "example": "$ passwd\nChanging password for user john.\nCurrent password:\nNew password:\nRetype new password:",
        "category": "User Management"
    },
    {
        "id": 4,
        "question": "Which command displays the actual type of a file by examining its contents?",
        "answer": "file",
        "example": "$ file /bin/ls\n/bin/ls: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), dynamically linked...",
        "category": "File Operations"
    },
    {
        "id": 5,
        "question": "How do you view the contents of a file?",
        "answer": "Use the cat command followed by the file path.",
        "example": "$ cat /etc/passwd\nroot:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n...",
        "category": "File Operations"
    },
    {
        "id": 6,
        "question": "How do you view the first 10 lines of a file?",
        "answer": "Use head followed by the file path.",
        "example": "$ head /var/log/syslog\nOct 18 14:55:03 hostname systemd[1]: Started Session 1 of user john.\nOct 18 14:55:05 hostname sshd[1234]: Accepted password for john from 192.168.1.2 port 54321\n...",
        "category": "File Operations"
    },
    {
        "id": 7,
        "question": "How do you view the last 3 lines of a file?",
        "answer": "Use tail -n 3 followed by the file path.",
        "example": "$ tail -n 3 /etc/passwd\nsshd:x:74:74:Privilege-separated SSH:/var/empty/sshd:/sbin/nologin\njohn:x:1001:1001:John Doe,,,:/home/john:/bin/bash",
        "category": "File Operations"
    },
    {
        "id": 8,
        "question": "What command counts lines, words, and characters in a file?",
        "answer": "wc (word count)",
        "example": "$ wc /etc/hosts\n  12   22  178 /etc/hosts\nLines: 12\nWords: 22\nCharacters: 178",
        "category": "File Operations"
    },
    {
        "id": 9,
        "question": "How do you write a long command over multiple lines in the terminal?",
        "answer": "Use a backslash \\ at the end of each line to continue the command.",
        "example": "$ echo \"This is a \\\n> multi-line \\\n> command\"\nThis is a multi-line command",
        "category": "Command Line Basics"
    },
    {
        "id": 10,
        "question": "How do you display your command history?",
        "answer": "Use the history command.",
        "example": "$ history\n   1  ls -l\n   2  cd /etc\n   3  cat passwd\n   4  history",
        "category": "Command History"
    },
    {
        "id": 11,
        "question": "How do you run the last command that started with \"ls\"?",
        "answer": "Use !ls",
        "example": "$ ls -l /etc\n... (output of the ls command)\n$ pwd\n/etc\n$ !ls\nls -l /etc\n... (executes ls -l /etc again)",
        "category": "Command History"
    },
    {
        "id": 12,
        "question": "How do you re-run the 26th command in the history list?",
        "answer": "Use !26",
        "example": "$ history\n...\n  26  ping google.com\n...\n$ !26\nping google.com\n... (executes the ping command)",
        "category": "Command History"
    },
    {
        "id": 13,
        "question": "What keyboard shortcut moves the cursor to the beginning of the command line?",
        "answer": "Ctrl+A",
        "example": "If you're typing a command and want to move the cursor to the start, press Ctrl+A.",
        "category": "Keyboard Shortcuts"
    },
    {
        "id": 14,
        "question": "What keyboard shortcut moves the cursor to the end of the command line?",
        "answer": "Ctrl+E",
        "example": "While editing a command, press Ctrl+E to move the cursor to the end.",
        "category": "Keyboard Shortcuts"
    },
    {
        "id": 15,
        "question": "What shortcut clears all text from the cursor to the beginning of the command line?",
        "answer": "Ctrl+U",
        "example": "Position the cursor where you want to start clearing, then press Ctrl+U.",
        "category": "Keyboard Shortcuts"
    },
    {
        "id": 16,
        "question": "What shortcut clears all text from the cursor to the end of the command line?",
        "answer": "Ctrl+K",
        "example": "Place the cursor at the starting point, press Ctrl+K to delete to the end.",
        "category": "Keyboard Shortcuts"
    },
    {
        "id": 17,
        "question": "What shortcut moves the cursor to the beginning of the previous word?",
        "answer": "Alt+B or Esc then B",
        "example": "While typing, press Alt+B to move back one word.",
        "category": "Keyboard Shortcuts"
    },
    {
        "id": 18,
        "question": "What shortcut moves the cursor to the end of the next word?",
        "answer": "Alt+F or Esc then F",
        "example": "Press Alt+F to move forward one word.",
        "category": "Keyboard Shortcuts"
    },
    {
        "id": 19,
        "question": "What shortcut searches your command history for a specific pattern?",
        "answer": "Ctrl+R",
        "example": "Press Ctrl+R, then start typing the pattern to search.\nThe terminal will display the matching command.",
        "category": "Keyboard Shortcuts"
    },
    {
        "id": 20,
        "question": "How do you execute multiple commands on a single line?",
        "answer": "Separate the commands with a semicolon ;.",
        "example": "$ cd /var/log; ls; pwd\nChanges directory to /var/log\nLists files in /var/log\nDisplays the current directory",
        "category": "Command Line Basics"
    }
]

# Simulated command outputs for restricted commands
SIMULATED_OUTPUTS = {
    "passwd": "Changing password for user john.\nNew password: \nRetype new password: \npasswd: all authentication tokens updated successfully.",
    "sudo": "Sorry, user john is not allowed to execute commands as root on localhost."
}

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

@app.route('/api/execute', methods=['POST'])
def execute_command():
    """Handle command execution or simulation"""
    data = request.get_json()
    command = data.get('command', '').strip()
    
    # Check if command is in simulated outputs
    if command in SIMULATED_OUTPUTS:
        return jsonify({
            "output": SIMULATED_OUTPUTS[command],
            "simulated": True
        })
    
    # For demonstration, return some safe commands
    if command == "whoami":
        return jsonify({
            "output": "john",
            "simulated": False
        })
    elif command == "date":
        from datetime import datetime
        return jsonify({
            "output": datetime.now().strftime("%c"),
            "simulated": False
        })
    
    # Default response for unknown commands
    return jsonify({
        "output": f"Command '{command}' not supported in demo mode.",
        "simulated": True
    })

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Return unique categories from flashcards"""
    categories = list(set(card["category"] for card in FLASHCARDS))
    return jsonify(categories)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
