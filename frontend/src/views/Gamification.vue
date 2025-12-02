<template>
  <v-container>
    <v-row>
      <v-col>
        <v-card>
          <v-card-title>🎮 Gamification & Rewards</v-card-title>
          <v-card-text>
            <div class="text-center">
              <p class="text-h4">Level {{ level }}</p>
              <p class="text-subtitle-1">{{ xp }} XP</p>
              <v-progress-linear :model-value="xp % 100" height="20"></v-progress-linear>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card>
          <v-card-title>🏆 Achievements</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item v-for="(achievement, index) in achievements" :key="index">
                <v-list-item-title>{{ achievement.title }}</v-list-item-title>
                <v-list-item-subtitle>{{ achievement.description }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const level = ref(0)
const xp = ref(0)
const achievements = ref([
  {
    title: "🎯 First Focus Session",
    description: "Completed your first focused work session"
  },
  {
    title: "⏰ Time Master",
    description: "Accumulated XP through focused work"
  },
  {
    title: "🚀 Consistency Champion",
    description: "Maintained focus across multiple sessions"
  }
])

async function getXP() {
  try {
    const response = await axios.get('http://localhost:8000/api/xp')
    xp.value = response.data.XP
    level.value = Math.floor(xp.value / 100) + 1
  } catch (error) {
    console.error('Error fetching XP:', error)
  }
}

onMounted(() => {
  getXP()
})
</script>
