<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useObjectLensApi } from "../../composables/useObjectLensApi";
import { Search, HelpCircle, Activity, ShieldCheck, AlertCircle, Sun, Moon, Laptop } from "@lucide/vue";

const api = useObjectLensApi();
const route = useRoute();
const router = useRouter();

const backendHealthy = ref(true);
const isSearchOpen = ref(false);

const themeMode = ref<"light" | "dark" | "auto">("auto");
let darkModeQuery: MediaQueryList | null = null;

function resolvedTheme(mode: typeof themeMode.value) {
  if (mode !== "auto") return mode;
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(mode: typeof themeMode.value) {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.theme = resolvedTheme(mode);
  document.documentElement.dataset.themeMode = mode;
  localStorage.setItem("objectlens-theme", mode);
}

function setTheme(mode: typeof themeMode.value) {
  themeMode.value = mode;
  applyTheme(mode);
}

const breadcrumbs = computed(() => {
  const parts = route.path.split("/").filter(Boolean);
  const list = [{ name: "Home", path: "/" }];
  
  let currentPath = "";
  parts.forEach((part, index) => {
    currentPath += `/${part}`;
    
    // Clean up names for display
    let name = decodeURIComponent(part);
    if (name === "providers") name = "Providers";
    if (name === "buckets") name = "Buckets";
    if (name === "details") name = "Details";
    if (name === "upload") name = "Upload Queue";
    
    list.push({
      name,
      path: currentPath
    });
  });
  
  return list;
});

async function checkHealth() {
  try {
    const res = await api.health();
    backendHealthy.value = res.status === "ok";
  } catch {
    backendHealthy.value = false;
  }
}

let healthTimer: ReturnType<typeof setInterval>;

onMounted(() => {
  checkHealth();
  healthTimer = setInterval(checkHealth, 10000); // Check every 10s
  
  // Theme initialization
  const stored = localStorage.getItem("objectlens-theme") as typeof themeMode.value | null;
  if (stored === "light" || stored === "dark" || stored === "auto") {
    themeMode.value = stored;
  }
  darkModeQuery = window.matchMedia("(prefers-color-scheme: dark)");
  darkModeQuery.addEventListener("change", () => {
    if (themeMode.value === "auto") applyTheme("auto");
  });
  applyTheme(themeMode.value);

  // Bind global keyboard shortcut: Ctrl/Cmd + K or /
  window.addEventListener("keydown", handleKeyDown);
});

onUnmounted(() => {
  clearInterval(healthTimer);
  window.removeEventListener("keydown", handleKeyDown);
});

function handleKeyDown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key === "k") {
    e.preventDefault();
    triggerSearch();
  }
}

function triggerSearch() {
  router.push("/search");
}
</script>

<template>
  <header class="topnav-container" aria-label="Breadcrumbs and Status">
    <!-- Breadcrumbs -->
    <nav class="breadcrumbs" aria-label="Breadcrumb navigation">
      <span v-for="(crumb, idx) in breadcrumbs" :key="crumb.path" class="breadcrumb-item">
        <NuxtLink :to="crumb.path" class="breadcrumb-link">
          {{ crumb.name }}
        </NuxtLink>
        <span v-if="idx < breadcrumbs.length - 1" class="breadcrumb-separator">/</span>
      </span>
    </nav>

    <!-- Right Side Tools -->
    <div class="topnav-actions">
      <!-- Search Input box trigger -->
      <button class="topnav-search-trigger" type="button" @click="triggerSearch">
        <Search :size="15" class="search-icon" />
        <span class="search-placeholder">Quick search...</span>
        <kbd class="search-kbd">⌘K</kbd>
      </button>

      <!-- Live health check status -->
      <div class="health-status-pills">
        <span class="health-status-badge" :class="backendHealthy ? 'healthy' : 'unhealthy'">
          <ShieldCheck v-if="backendHealthy" :size="14" />
          <AlertCircle v-else :size="14" />
          <span>{{ backendHealthy ? 'API Active' : 'API Offline' }}</span>
        </span>
      </div>

      <!-- Theme Select Hover Dropdown -->
      <div class="theme-menu-container">
        <button class="theme-menu-current" type="button" data-tooltip="Theme Mode">
          <span v-if="themeMode === 'light'"><Sun :size="16" /></span>
          <span v-else-if="themeMode === 'dark'"><Moon :size="16" /></span>
          <span v-else-if="themeMode === 'auto'"><Laptop :size="16" /></span>
        </button>
        <div class="theme-menu-dropdown">
          <button :class="{ active: themeMode === 'light' }" type="button" @click="setTheme('light')">
            <Sun :size="14" /> Light
          </button>
          <button :class="{ active: themeMode === 'dark' }" type="button" @click="setTheme('dark')">
            <Moon :size="14" /> Dark
          </button>
          <button :class="{ active: themeMode === 'auto' }" type="button" @click="setTheme('auto')">
            <Laptop :size="14" /> Auto
          </button>
        </div>
      </div>

      <!-- Docs / Help link -->
      <a href="https://github.com/google/gemini-cli" target="_blank" class="topnav-icon-btn" title="Documentation">
        <HelpCircle :size="18" />
      </a>
    </div>
  </header>
</template>

<style scoped>
.theme-menu-container {
  margin-left: 4px;
}

.theme-menu-current {
  width: 32px;
  height: 32px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.theme-menu-dropdown {
  top: calc(100% + 4px);
  bottom: auto;
  left: auto;
  right: 0;
  width: 100px;
  box-shadow: 0 8px 24px rgb(15 23 42 / 12%);
}

/* Invisible pointer bridge to close the 4px hover gap */
.theme-menu-dropdown::before {
  content: "";
  position: absolute;
  top: -8px;
  left: 0;
  right: 0;
  height: 8px;
  background: transparent;
}

[data-theme="dark"] .theme-menu-dropdown {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}
</style>
