import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Timer from '../views/Timer.vue'
import History from '../views/History.vue'
import Gamification from '../views/Gamification.vue'
import Settings from '../views/Settings.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Dashboard',
      component: Dashboard,
    },
    {
      path: '/timer',
      name: 'Timer',
      component: Timer,
    },
    {
      path: '/history',
      name: 'History',
      component: History,
    },
    {
      path: '/gamification',
      name: 'Gamification',
      component: Gamification,
    },
    {
      path: '/settings',
      name: 'Settings',
      component: Settings,
    },
  ],
})

export default router
