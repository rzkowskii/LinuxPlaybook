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
              <h2 class="flashcard-question">{{ currentFlashcard.question }}</h2>
              <div class="flashcard-answer">{{ currentFlashcard.answer }}</div>
              <pre class="flashcard-example">{{ currentFlashcard.example }}</pre>
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
        <div class="terminal-container h-[600px]">
          <div ref="terminal" class="h-full"></div>
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
const xtermInstance = ref<Terminal | null>(null)
const flashcards = ref<any[]>([])
const categories = ref<string[]>([])

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
const initializeTerminal = () => {
  if (!terminal.value) return

  xtermInstance.value = new Terminal({
    cursorBlink: true,
    theme: {
      background: '#1a1b26',
      foreground: '#a9b1d6'
    }
  })

  const fitAddon = new FitAddon()
  const webLinksAddon = new WebLinksAddon()

  xtermInstance.value.loadAddon(fitAddon)
  xtermInstance.value.loadAddon(webLinksAddon)
  xtermInstance.value.open(terminal.value)
  fitAddon.fit()

  xtermInstance.value.writeln('RHCSA Interactive Terminal')
  xtermInstance.value.writeln('Type commands to interact with the system')
  xtermInstance.value.writeln('')
  xtermInstance.value.write('$ ')
  
  let currentLine = ''
  xtermInstance.value.onKey(({ key, domEvent }) => {
    const char = key
    
    if (domEvent.keyCode === 13) { // Enter key
      executeCommand(currentLine)
      currentLine = ''
      return
    }
    
    if (domEvent.keyCode === 8) { // Backspace
      if (currentLine.length > 0) {
        currentLine = currentLine.slice(0, -1)
        xtermInstance.value?.write('\b \b')
      }
      return
    }
    
    currentLine += char
    xtermInstance.value?.write(char)
  })
}

const executeCommand = async (command: string) => {
  if (!xtermInstance.value) return
  
  xtermInstance.value.writeln('')
  try {
    const response = await axios.post(`${API_BASE_URL}/api/execute`, { command })
    xtermInstance.value.writeln(response.data.output)
  } catch (error) {
    xtermInstance.value.writeln('Error executing command')
  }
  xtermInstance.value.write('\n$ ')
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
