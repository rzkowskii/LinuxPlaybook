# LinuxPlaybook

An interactive learning platform for Linux commands featuring flashcards and a live terminal interface.

## Features

- Interactive flashcards with Linux commands
- Live terminal interface using xterm.js
- Command simulation for restricted operations
- Search and filter capabilities
- Responsive split-view design

## Tech Stack

- Frontend:
  - Vue.js + TypeScript
  - TailwindCSS for styling
  - xterm.js for terminal emulation
- Backend:
  - Flask (Python)
  - Flask-CORS for cross-origin support

## Prerequisites

- Node.js (v14+)
- Python (v3.8+)
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/rzkowskii/LinuxPlaybook.git
cd LinuxPlaybook
```

2. Install root dependencies:
```bash
npm install
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

4. Set up Python virtual environment and install backend dependencies:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

## Development

Start both frontend and backend development servers:

```bash
npm run dev
```

This will start:
- Frontend server at http://localhost:5173
- Backend server at http://localhost:5001

## Adding New Flashcards

Add new flashcards by updating the `FLASHCARDS` array in `backend/app.py`. Each flashcard should follow this format:

```python
{
    "id": <unique_number>,
    "question": "What command...",
    "answer": "Command description...",
    "example": "$ command\noutput",
    "category": "Category Name"
}
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
