<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { Trophy, LayoutDashboard, Menu, X } from 'lucide-vue-next'

const isMobileMenuOpen = ref(false)
const route = useRoute()

// A quick helper function to highlight the active tab
const isActive = (path: string) => route.path === path
</script>

<template>
  <nav class="bg-slate-900 border-b border-slate-700 sticky top-0 z-50 shadow-md mb-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        
        <div class="flex items-center">
          <RouterLink to="/" class="flex items-center gap-2 group">
            <div class="bg-emerald-500/10 p-2 rounded-lg group-hover:bg-emerald-500/20 transition-colors">
              <Trophy class="w-6 h-6 text-emerald-400" />
            </div>
            <span class="font-bold text-xl tracking-tight text-white group-hover:text-emerald-300 transition-colors">
                Fantasy Power Rankings
            </span>
          </RouterLink>
        </div>

        <div class="hidden md:flex items-center space-x-1">
          <RouterLink 
            to="/" 
            class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
            :class="isActive('/') ? 'bg-slate-800 text-emerald-400' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
          >
            <LayoutDashboard class="w-4 h-4" />
            Dashboard
          </RouterLink>
        </div>

        <div class="flex items-center md:hidden">
          <button 
            @click="isMobileMenuOpen = !isMobileMenuOpen"
            class="p-2 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 focus:outline-none"
          >
            <Menu v-if="!isMobileMenuOpen" class="w-6 h-6" />
            <X v-else class="w-6 h-6" />
          </button>
        </div>
      </div>
    </div>

    <div v-show="isMobileMenuOpen" class="md:hidden border-t border-slate-700 bg-slate-900">
      <div class="px-2 pt-2 pb-3 space-y-1 sm:px-3">
        <RouterLink 
          to="/" 
          @click="isMobileMenuOpen = false"
          class="flex items-center gap-3 px-3 py-2 rounded-md text-base font-medium"
          :class="isActive('/') ? 'bg-slate-800 text-emerald-400' : 'text-slate-300 hover:bg-slate-800 hover:text-white'"
        >
          <LayoutDashboard class="w-5 h-5" />
          Dashboard
        </RouterLink>
      </div>
    </div>
  </nav>
</template>