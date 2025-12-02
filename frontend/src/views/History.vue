<template>
  <v-container>
    <v-row>
      <v-col>
        <v-card>
          <v-card-title>🚫 Distraction History</v-card-title>
          <v-card-text>
            <v-table>
              <thead>
                <tr>
                  <th class="text-left">URL</th>
                  <th class="text-left">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in history" :key="index">
                  <td>{{ item[0] }}</td>
                  <td>{{ item[1] }}</td>
                </tr>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const history = ref([])

async function getHistory() {
  try {
    const response = await axios.get('http://localhost:8000/api/history')
    history.value = response.data.Distractions
  } catch (error) {
    console.error('Error fetching history:', error)
  }
}

onMounted(() => {
  getHistory()
})
</script>
