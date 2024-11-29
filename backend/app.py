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
    # Original 1-20 flashcards
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
    },
    # Additional flashcards 21-46
    {
        "id": 21,
        "question": "How do you display the current time in 24-hour format?",
        "answer": "Use date '+%H:%M' or date +%R",
        "example": "$ date '+%H:%M'\n14:55\n$ date +%R\n14:55",
        "category": "System Information"
    },
    {
        "id": 22,
        "question": "How do you display the current date in MM/DD/YYYY format?",
        "answer": "Use date '+%m/%d/%Y'",
        "example": "$ date '+%m/%d/%Y'\n10/18/2023",
        "category": "System Information"
    },
    {
        "id": 23,
        "question": "How do you display the type of the /etc/passwd file?",
        "answer": "Use file /etc/passwd",
        "example": "$ file /etc/passwd\n/etc/passwd: ASCII text",
        "category": "File Operations"
    },
    {
        "id": 24,
        "question": "What command do you use to display the type of the /bin/passwd file?",
        "answer": "Use file /bin/passwd",
        "example": "$ file /bin/passwd\n/bin/passwd: setuid ELF 64-bit LSB shared object, x86-64, version 1 (SYSV)...",
        "category": "File Operations"
    },
    {
        "id": 25,
        "question": "How do you display the type of the /home directory?",
        "answer": "Use file /home",
        "example": "$ file /home\n/home: directory",
        "category": "File Operations"
    },
    {
        "id": 26,
        "question": "How do you view the contents of multiple files?",
        "answer": "Use cat followed by the file names.",
        "example": "$ cat file1.txt file2.txt\n... (contents of file1.txt)\n... (contents of file2.txt)",
        "category": "File Operations"
    },
    {
        "id": 27,
        "question": "How do you view the first 3 lines of the /etc/passwd file?",
        "answer": "Use head -n 3 /etc/passwd",
        "example": "$ head -n 3 /etc/passwd\nroot:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\nbin:x:2:2:bin:/bin:/usr/sbin/nologin",
        "category": "File Operations"
    },
    {
        "id": 28,
        "question": "What command displays the last 10 lines of a file by default?",
        "answer": "tail followed by the file name.",
        "example": "$ tail /var/log/syslog\n... (last 10 lines of syslog)",
        "category": "File Operations"
    },
    {
        "id": 29,
        "question": "How do you count lines, words, and characters in the /etc/passwd file?",
        "answer": "Use wc /etc/passwd",
        "example": "$ wc /etc/passwd\n  45   63 1935 /etc/passwd\nLines: 45\nWords: 63\nCharacters: 1935",
        "category": "File Operations"
    },
    {
        "id": 30,
        "question": "What command counts the number of lines in /etc/passwd and /etc/group?",
        "answer": "Use wc -l followed by the file names.",
        "example": "$ wc -l /etc/passwd /etc/group\n  45 /etc/passwd\n  60 /etc/group\n 105 total",
        "category": "File Operations"
    },
    {
        "id": 31,
        "question": "How do you count the number of characters in /etc/group and /etc/hosts?",
        "answer": "Use wc -c followed by the file names.",
        "example": "$ wc -c /etc/group /etc/hosts\n 2030 /etc/group\n  178 /etc/hosts\n 2208 total",
        "category": "File Operations"
    },
    {
        "id": 32,
        "question": "What is the command to display the first 3 lines of two files using backslashes to continue the command?",
        "answer": "Use head -n 3 followed by backslashes and file names.",
        "example": "$ head -n 3 \\\n> /usr/share/dict/words \\\n> /usr/share/dict/linux.words\n==> /usr/share/dict/words <==\nA\na\naa\n\n==> /usr/share/dict/linux.words <==\n4th\nAbbas\nabbey",
        "category": "File Operations"
    },
    {
        "id": 33,
        "question": "What is the function of the exclamation point ! character in the command line?",
        "answer": "It is used to recall and execute commands from your history.",
        "example": "!! repeats the last command.\n!n executes the command with history number n.\n!string executes the last command starting with string.",
        "category": "Command History"
    },
    {
        "id": 34,
        "question": "How do you recall and execute the 20th command from the history list?",
        "answer": "Use !20",
        "example": "$ !20\n... (executes command number 20)",
        "category": "Command History"
    },
    {
        "id": 35,
        "question": "What does the !number command do?",
        "answer": "It executes the command corresponding to that number in the history list.",
        "example": "$ !42\n... (executes command number 42 from history)",
        "category": "Command History"
    },
    {
        "id": 36,
        "question": "What does the !string command do?",
        "answer": "It executes the most recent command that begins with the specified string.",
        "example": "$ !ls\n... (executes the most recent command starting with 'ls')",
        "category": "Command History"
    },
    {
        "id": 37,
        "question": "How do you clear from the cursor to the beginning of the command line using a shortcut?",
        "answer": "Press Ctrl+U",
        "example": "Place the cursor where you want to start clearing, then press Ctrl+U.",
        "category": "Keyboard Shortcuts"
    },
    {
        "id": 38,
        "question": "What shortcut searches the history list of commands for a pattern?",
        "answer": "Ctrl+R",
        "example": "Press Ctrl+R and type the search pattern.",
        "category": "Keyboard Shortcuts"
    },
    {
        "id": 39,
        "question": "How do you jump to the beginning of the previous word on the command line?",
        "answer": "Press Alt+B or Esc then B",
        "example": "Use this to navigate back one word at a time while editing a command.",
        "category": "Keyboard Shortcuts"
    },
    {
        "id": 40,
        "question": "What does Ctrl+A do in the command line?",
        "answer": "Jumps to the beginning of the command line.",
        "example": "Press Ctrl+A to move cursor to start of line.",
        "category": "Keyboard Shortcuts"
    },
    {
        "id": 41,
        "question": "What does Ctrl+E do in the command line?",
        "answer": "Jumps to the end of the command line.",
        "example": "Press Ctrl+E to move cursor to end of line.",
        "category": "Keyboard Shortcuts"
    },
    {
        "id": 42,
        "question": "What does Ctrl+U do in the command line?",
        "answer": "Clears all text from the cursor to the beginning of the command line.",
        "example": "Press Ctrl+U to delete from cursor to start of line.",
        "category": "Keyboard Shortcuts"
    },
    {
        "id": 43,
        "question": "What does Ctrl+K do in the command line?",
        "answer": "Clears all text from the cursor to the end of the command line.",
        "example": "Press Ctrl+K to delete from cursor to end of line.",
        "category": "Keyboard Shortcuts"
    },
    {
        "id": 44,
        "question": "What does Ctrl+LeftArrow do in the command line?",
        "answer": "Moves the cursor backward one word.",
        "example": "Note: Depending on the terminal, you might need to use Alt+B instead.",
        "category": "Keyboard Shortcuts"
    },
    {
        "id": 45,
        "question": "What does Ctrl+RightArrow do in the command line?",
        "answer": "Moves the cursor forward one word.",
        "example": "Note: Depending on the terminal, you might need to use Alt+F instead.",
        "category": "Keyboard Shortcuts"
    },
    {
        "id": 46,
        "question": "What does Ctrl+R do in the command line?",
        "answer": "Initiates a reverse search in your command history for a pattern.",
        "example": "Press Ctrl+R and type to search command history.",
        "category": "Keyboard Shortcuts"
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
