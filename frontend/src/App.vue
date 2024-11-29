<template>
  <div class="min-h-screen bg-gray-100">
    <header class="bg-white shadow">
      <div class="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        <h1 class="text-3xl font-bold text-gray-900">RHCSA Interactive Playbook</h1>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Flashcard Section -->
        <div class="space-y-6">
          <div class="bg-white rounded-lg shadow p-6">
            <!-- Search and Filter -->
            <div class="space-y-4 mb-6">
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Search flashcards..."
                class="search-bar"
              />
              <select
                v-model="selectedCategory"
                class="category-filter"
              >
                <option value="">All Categories</option>
                <option
                  v-for="category in categories"
                  :key="category"
                  :value="category"
                >
                  {{ category }}
                </option>
              </select>
            </div>

            <!-- Current Flashcard -->
            <div class="flashcard">
              <h2 class="flashcard-question break-words">{{ currentFlashcard.question }}</h2>
              <div class="flashcard-answer break-words">{{ currentFlashcard.answer }}</div>
              <pre class="flashcard-example whitespace-pre-wrap break-words">{{ currentFlashcard.example }}</pre>
            </div>

            <!-- Navigation Controls -->
            <div class="nav-controls">
              <button
                @click="previousCard"
                class="btn btn-secondary"
                :disabled="currentIndex === 0"
              >
                Previous
              </button>
              <span class="text-gray-600">
                {{ currentIndex + 1 }} / {{ filteredFlashcards.length }}
              </span>
              <button
                @click="nextCard"
                class="btn btn-secondary"
                :disabled="currentIndex === filteredFlashcards.length - 1"
              >
                Next
              </button>
            </div>
          </div>
        </div>

        <!-- Terminal Section -->
        <div class="terminal-container h-[600px]" @click="focusTerminal">
          <div ref="terminal" class="h-full"></div>
          <textarea
            ref="terminalInput"
            class="terminal-input"
            @keydown="handleKeyDown"
            @input="handleInput"
            v-model="lineBuffer"
          ></textarea>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import { WebLinksAddon } from 'xterm-addon-web-links'
import axios from 'axios'
import 'xterm/css/xterm.css'

// API base URL
const API_BASE_URL = 'http://localhost:5001'

// State
const searchQuery = ref('')
const selectedCategory = ref('')
const currentIndex = ref(0)
const terminal = ref<HTMLElement | null>(null)
const terminalInput = ref<HTMLTextAreaElement | null>(null)
const xtermInstance = ref<Terminal | null>(null)
const flashcards = ref<any[]>([])
const categories = ref<string[]>([])
const currentCommand = ref('')
const isPasswordInput = ref(false)
const lineBuffer = ref('')

// Computed
const filteredFlashcards = computed(() => {
  return flashcards.value.filter(card => {
    const matchesSearch = card.question.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                         card.answer.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesCategory = !selectedCategory.value || card.category === selectedCategory.value
    return matchesSearch && matchesCategory
  })
})

const currentFlashcard = computed(() => {
  return filteredFlashcards.value[currentIndex.value] || {
    question: 'No flashcard found',
    answer: '',
    example: ''
  }
})

// Methods
const focusTerminal = () => {
  if (terminalInput.value) {
    terminalInput.value.focus()
  }
}

const writePrompt = (isInitial = false) => {
  if (!xtermInstance.value) return
  if (isInitial) {
    xtermInstance.value.writeln('')
    xtermInstance.value.write('$ ')
  } else {
    xtermInstance.value.writeln('')
    xtermInstance.value.write('$ ')
  }
}

const handleCommand = async (command: string) => {
  if (!xtermInstance.value) return
  
  try {
    // Clean the command input
    const cleanCommand = command.trim().replace(/\s+/g, ' ')
    
    const response = await axios.post(`${API_BASE_URL}/api/execute`, { command: cleanCommand })
    
    // Handle password prompts
    if (response.data.prompt && response.data.prompt.includes('password')) {
      isPasswordInput.value = true
      xtermInstance.value.write(response.data.output)
    } else {
      isPasswordInput.value = false
      
      // Write command output with proper line handling
      if (response.data.output) {
        xtermInstance.value.writeln(response.data.output)
      }
      
      // Check if the command matches the current flashcard's example
      const expectedCommand = currentFlashcard.value.example.split('\n')[0].trim().replace('$ ', '')
      if (cleanCommand === expectedCommand.trim()) {
        // Check for command success
        if (response.data.success) {
          setTimeout(() => {
            nextCard()
            writePrompt()
          }, 1000)
        } else {
          writePrompt()
        }
      } else {
        writePrompt()
      }
    }
  } catch (error) {
    xtermInstance.value.writeln('Error executing command')
    writePrompt()
    isPasswordInput.value = false
  }
}

const handleKeyDown = async (event: KeyboardEvent) => {
  if (event.key === 'Enter') {
    event.preventDefault()
    const command = lineBuffer.value
    lineBuffer.value = ''
    if (xtermInstance.value) {
      xtermInstance.value.write('\r\n')
      await handleCommand(command)
    }
  } else if (event.key === 'Backspace' || event.key === 'Delete') {
    event.preventDefault()
    if (lineBuffer.value.length > 0) {
      lineBuffer.value = lineBuffer.value.slice(0, -1)
      if (!isPasswordInput.value && xtermInstance.value) {
        xtermInstance.value.write('\b \b')
      }
    }
  }
}

const handleInput = (event: Event) => {
  const target = event.target as HTMLTextAreaElement
  const value = target.value
  const lastChar = value.slice(-1)

  if (xtermInstance.value) {
    if (isPasswordInput.value) {
      // Don't display password characters
      xtermInstance.value.write('*')
    } else {
      // Only write printable characters
      if (lastChar && lastChar.match(/[\x20-\x7E]/)) {
        xtermInstance.value.write(lastChar)
      }
    }
  }
}

const initializeTerminal = () => {
  if (!terminal.value) return

  xtermInstance.value = new Terminal({
    cursorBlink: true,
    theme: {
      background: '#1a1b26',
      foreground: '#a9b1d6',
      cursor: '#a9b1d6'
    },
    fontSize: 14,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    rows: 24,
    convertEol: true,
    cursorStyle: 'block'
  })

  const fitAddon = new FitAddon()
  const webLinksAddon = new WebLinksAddon()

  xtermInstance.value.loadAddon(fitAddon)
  xtermInstance.value.loadAddon(webLinksAddon)
  xtermInstance.value.open(terminal.value)
  fitAddon.fit()

  xtermInstance.value.writeln('RHCSA Interactive Terminal')
  xtermInstance.value.writeln('Type commands to interact with the system')
  writePrompt(true)

  // Focus terminal input
  focusTerminal()
}

const fetchFlashcards = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/flashcards`)
    flashcards.value = response.data
  } catch (error) {
    console.error('Error fetching flashcards:', error)
  }
}

const fetchCategories = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/categories`)
    categories.value = response.data
  } catch (error) {
    console.error('Error fetching categories:', error)
  }
}

const nextCard = () => {
  if (currentIndex.value < filteredFlashcards.value.length - 1) {
    currentIndex.value++
  }
}

const previousCard = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

// Lifecycle
onMounted(() => {
  initializeTerminal()
  fetchFlashcards()
  fetchCategories()
  
  window.addEventListener('resize', () => {
    const fitAddon = new FitAddon()
    if (xtermInstance.value) {
      xtermInstance.value.loadAddon(fitAddon)
      fitAddon.fit()
    }
  })
})
</script>

<style>
.flashcard-question {
  @apply text-xl font-semibold text-gray-800 mb-4 break-words;
}

.flashcard-answer {
  @apply text-gray-600 mb-4 break-words;
}

.flashcard-example {
  @apply bg-gray-100 rounded p-4 font-mono text-sm whitespace-pre-wrap break-words overflow-x-auto;
  max-width: 100%;
}

.terminal-container {
  @apply bg-[#1a1b26] rounded-lg overflow-hidden outline-none cursor-text relative;
}

.terminal-container .xterm {
  @apply p-4;
}

.terminal-container .xterm-viewport {
  @apply !bg-[#1a1b26];
}

.terminal-container .xterm-screen {
  @apply !bg-[#1a1b26];
}

.terminal-input {
  @apply absolute opacity-0 left-0 top-0 w-0 h-0 overflow-hidden;
}

.flashcard {
  @apply overflow-hidden;
  word-wrap: break-word;
  word-break: break-word;
}

.xterm-rows {
  line-height: 1.2;
}

.xterm-helper-textarea {
  left: 0 !important;
}
</style>
