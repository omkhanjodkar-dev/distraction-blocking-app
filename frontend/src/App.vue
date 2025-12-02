<template>
  <v-app>
    <v-navigation-drawer v-model="drawer" app>
      <v-list>
        <v-list-item to="/">
          <v-list-item-title>Dashboard</v-list-item-title>
        </v-list-item>
        <v-list-item to="/timer">
          <v-list-item-title>Timer</v-list-item-title>
        </v-list-item>
        <v-list-item to="/history">
          <v-list-item-title>History</v-list-item-title>
        </v-list-item>
        <v-list-item to="/gamification">
          <v-list-item-title>Gamification</v-list-item-title>
        </v-list-item>
        <v-list-item to="/settings">
          <v-list-item-title>Settings</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-app-bar app>
      <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>
      <v-toolbar-title>Focus App</v-toolbar-title>
    </v-app-bar>

    <v-main>
      <router-view></router-view>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const drawer = ref(false)
</script>
