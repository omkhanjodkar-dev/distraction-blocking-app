<template>
  <v-container>
    <v-row>
      <v-col>
        <v-card>
          <v-card-title>⚙️ Settings</v-card-title>
          <v-card-text>
            <v-select
              label="Intervention Style"
              :items="['nudge', 'auto-close']"
              v-model="settings.intervention_style"
            ></v-select>
            <v-text-field
              label="Session Time (minutes)"
              type="number"
              v-model.number="settings.session_time"
            ></v-text-field>
            <v-textarea
              label="Context Paragraph"
              v-model="settings.context_paragraph"
            ></v-textarea>
            <v-btn @click="saveSettings">Save</v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const settings = ref({
  intervention_style: 'nudge',
  session_time: 25,
  context_paragraph: ''
})

async function getSettings() {
  try {
    const response = await axios.get('http://localhost:8000/api/settings')
    settings.value.intervention_style = response.data['Intervention Style']
    settings.value.session_time = response.data['Session Time']
    settings.value.context_paragraph = response.data['context_paragraph']
  } catch (error) {
    console.error('Error fetching settings:', error)
  }
}

async function saveSettings() {
  try {
    await axios.post('http://localhost:8000/api/settings', {
      intervention_style: settings.value.intervention_style,
      session_time: settings.value.session_time,
      context_paragraph: settings.value.context_paragraph
    })
    alert('Settings saved successfully!')
  } catch (error) {
    console.error('Error saving settings:', error)
    alert('Error saving settings.')
  }
}

onMounted(() => {
  getSettings()
})
</script>
