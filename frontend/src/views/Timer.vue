<template>
  <v-container>
    <v-row>
      <v-col>
        <v-card>
          <v-card-text class="text-center">
            <div class="text-h1">{{ formatTime(timeLeft) }}</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card>
          <v-card-text class="text-center">
            <p>{{ quote }}</p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card>
          <v-card-text>
            <v-progress-linear :model-value="progress" height="20"></v-progress-linear>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card>
          <v-card-title>📊 Today's Summary</v-card-title>
          <v-card-text>
            <p>⏱️ Time Focused: {{ timeFocused }} minutes</p>
            <p>🚫 Distractions: {{ distractions }}</p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col class="text-center">
        <v-btn @click="startTimer" v-if="!timerRunning">🚀 Start Focus Session</v-btn>
        <v-btn @click="stopTimer" v-else>🛑 Stop Focus Session</v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const timeLeft = ref(25 * 60)
const timerRunning = ref(false)
const quote = ref('')
const progress = ref(0)
const timeFocused = ref(0)
const distractions = ref(0)
let timerId: any = null

const quotes = [
  "Stay focused and never give up.",
  "Small steps lead to big results.",
  "Discipline is the bridge to success.",
  "Your future is created by what you do today.",
  "Push yourself, because no one else will."
]

function formatTime(seconds: number) {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}

function startTimer() {
  timerRunning.value = true
  timerId = setInterval(() => {
    timeLeft.value--
    progress.value = (25 * 60 - timeLeft.value) / (25 * 60) * 100
    if (timeLeft.value === 0) {
      stopTimer()
    }
  }, 1000)
}

function stopTimer() {
  timerRunning.value = false
  clearInterval(timerId)
}

async function getStats() {
  try {
    const sessionsResponse = await axios.get('http://localhost:8000/api/sessions')
    const distractionsResponse = await axios.get('http://localhost:8000/api/history')
    
    const today = new Date().toLocaleDateString()
    
    timeFocused.value = sessionsResponse.data.Sessions.filter((session: any) => new Date(session[1]).toLocaleDateString() === today).reduce((acc: number, session: any) => acc + session[0], 0)
    distractions.value = distractionsResponse.data.Distractions.filter((distraction: any) => new Date(distraction[1]).toLocaleDateString() === today).length
  } catch (error) {
    console.error('Error fetching stats:', error)
  }
}

onMounted(() => {
  quote.value = quotes[Math.floor(Math.random() * quotes.length)]
  getStats()
})
</script>
