<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import type {
  ProviderConnection,
  ProviderStatus,
} from "../../../composables/useObjectLensApi";
import { useObjectLensApi } from "../../../composables/useObjectLensApi";
import {
  Server,
  ShieldCheck,
  AlertCircle,
  Database,
  FolderOpen,
  ArrowRight,
  Settings,
  Activity,
  Cloud,
  Info,
} from "@lucide/vue";

const route = useRoute();
const api = useObjectLensApi();

const providerId = computed(() => String(route.params.providerId || ""));
const provider = ref<ProviderConnection | null>(null);
const status = ref<ProviderStatus | null>(null);
const loading = ref(true);
const error = ref("");

const runningDiagnostics = ref<"simple" | "deep" | null>(null);
const diagnosticError = ref("");

async function runDiagnostics(mode: "simple" | "deep") {
  runningDiagnostics.value = mode;
  diagnosticError.value = "";
  try {
    status.value = await api.providerStatus(providerId.value, mode);
  } catch (err) {
    diagnosticError.value = err instanceof Error ? err.message : `Failed to run ${mode} diagnostics.`;
  } finally {
    runningDiagnostics.value = null;
  }
}

const connectionChecks = computed(() => {
  if (!status.value?.capabilities) return [];
  return status.value.capabilities.filter(c => 
    c.name.includes("Connection")
  );
});

const bucketChecks = computed(() => {
  if (!status.value?.capabilities) return [];
  return status.value.capabilities.filter(c => 
    c.name.includes("Bucket") && !c.name.includes("Objects")
  );
});

const objectChecks = computed(() => {
  if (!status.value?.capabilities) return [];
  return status.value.capabilities.filter(c => 
    c.name.includes("Objects") || c.name.includes("Object")
  );
});

function getFeatureDescription(name: string): string {
  if (name.includes("Endpoint Connection")) {
    return "Validates client initialization and endpoint URL connectivity.";
  }
  if (name.includes("List Buckets")) {
    return "s3:ListAllMyBuckets - Authorizes listing all buckets on the S3 provider.";
  }
  if (name.includes("List Objects")) {
    return "s3:ListBucket - Authorizes querying object keys and prefix directories.";
  }
  if (name.includes("Upload Object")) {
    return "s3:PutObject - Authorizes uploading new files and writing content payloads.";
  }
  if (name.includes("Delete Object")) {
    return "s3:DeleteObject - Authorizes permanently deleting files from the bucket.";
  }
  return "S3 permission or connection capability check.";
}

onMounted(async () => {
  try {
    provider.value = await api.providerConnection(providerId.value);
    status.value = await api.providerStatus(providerId.value);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load provider details.";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="provider-diagnostics-page">
    <!-- Breadcrumb Path -->
    <nav class="breadcrumb real-breadcrumb" aria-label="Provider diagnostics path">
      <NuxtLink to="/">Dashboard</NuxtLink>
      <span class="breadcrumb-separator">/</span>
      <NuxtLink to="/providers">Providers</NuxtLink>
      <span class="breadcrumb-separator">/</span>
      <NuxtLink :to="`/providers/${encodeURIComponent(providerId)}`">
        {{ provider?.name || providerId }}
      </NuxtLink>
      <span class="breadcrumb-separator">/</span>
      <span class="current">Diagnostic Audit</span>
    </nav>

    <!-- Header Section -->
    <header class="page-title-section provider-diagnostics-header">
      <div class="header-text-block">
        <div class="title-with-icon-row flex-wrap gap-10">
          <Activity :size="24" class="text-accent flex-shrink-0" />
          <h1>Diagnostic Audit</h1>
          <span class="provider-type-badge">{{ provider?.type?.toUpperCase() || "S3" }}</span>
          <span class="provider-status-badge" :class="status?.status === 'healthy' ? 'healthy' : 'unhealthy'">
            <span class="status-dot-indicator" />
            <span>{{ status?.status === 'healthy' ? 'Healthy' : 'Offline' }}</span>
          </span>
        </div>
        <p class="subtitle mt-4">
          Detailed manual credential connection testing, policy audit, and CRUD S3 capability validation.
        </p>
      </div>
      <div class="header-actions flex-wrap gap-8">
        <NuxtLink
          class="btn btn-secondary flex-center gap-6"
          :to="`/providers/${encodeURIComponent(providerId)}/details`"
        >
          <Settings :size="14" />
          <span>Connection Parameters</span>
        </NuxtLink>
        <NuxtLink
          class="btn btn-primary flex-center gap-6"
          :to="`/providers/${encodeURIComponent(providerId)}`"
        >
          <FolderOpen :size="14" />
          <span>Explore Buckets</span>
        </NuxtLink>
      </div>
    </header>

    <!-- Loading & Error States -->
    <div v-if="loading" class="dashboard-skeleton-loader mt-24">
      <div class="skeleton-card" style="height: 120px;" v-for="i in 3" :key="i" />
    </div>
    
    <div v-else-if="error" class="error-panel mt-24">
      <div class="error-panel-icon">
        <Sliders :size="32" class="text-danger" />
      </div>
      <div class="error-panel-text">
        <h3>Diagnostics Loading Failed</h3>
        <p>ObjectLens could not initialize diagnostics for this provider connection.</p>
        <code class="error-log">{{ error }}</code>
      </div>
    </div>

    <!-- Diagnostics Audits Body -->
    <template v-else>
      <!-- Offline Warning Banner -->
      <div v-if="status?.status === 'unhealthy'" class="offline-alert-banner mb-24 p-16 border rounded bg-danger-soft flex-center-left gap-16">
        <div class="alert-icon-wrapper p-10 bg-danger-circle rounded-circle flex-shrink-0" style="background: rgba(239, 68, 68, 0.08); display: flex; align-items: center; justify-content: center;">
          <AlertCircle :size="20" class="text-danger" />
        </div>
        <div class="alert-content">
          <h4 class="margin-0 text-danger" style="font-size: 14px; font-weight: 700;">Provider is Offline or Unreachable</h4>
          <p class="margin-0 mt-4 text-muted" style="font-size: 12px; line-height: 1.4;">
            {{ status?.message || "ObjectLens cannot connect to the specified S3 endpoint. Check your credentials, network settings, and SSL certificate verification rules." }}
          </p>
        </div>
      </div>

      <!-- S3 Diagnostic Panel -->
      <section class="diagnostic-audit-wrapper">
        <article class="dashboard-content-block">
          <div class="block-header border-bottom pb-12 mb-16 flex-center-between flex-wrap gap-10">
            <div class="flex-center-left gap-10">
              <Activity :size="18" class="text-accent" />
              <h3 class="margin-0">S3 Access & Feature Diagnostic Audit</h3>
            </div>
            <div class="flex-center-left gap-8">
              <button 
                class="btn btn-secondary flex-center gap-6" 
                :disabled="runningDiagnostics !== null" 
                @click="runDiagnostics('simple')"
                type="button"
              >
                <Activity :size="14" :class="{ 'spin-loader': runningDiagnostics === 'simple' }" />
                <span>{{ runningDiagnostics === 'simple' ? 'Verifying...' : 'Verify Connection (Fast)' }}</span>
              </button>
              <button 
                class="btn btn-secondary flex-center gap-6" 
                :disabled="runningDiagnostics !== null" 
                @click="runDiagnostics('deep')"
                type="button"
              >
                <Activity :size="14" :class="{ 'spin-loader': runningDiagnostics === 'deep' }" />
                <span>{{ runningDiagnostics === 'deep' ? 'Running Audit...' : 'Run Full Capability Audit (Deep)' }}</span>
              </button>
            </div>
          </div>

          <div v-if="diagnosticError" class="error-banner mb-16 flex-center-left gap-8 p-12 border rounded bg-danger-soft">
            <AlertCircle :size="14" class="text-danger" />
            <span class="text-sm text-danger">{{ diagnosticError }}</span>
          </div>

          <p class="section-intro-text mb-20">
            ObjectLens performs manual connection and S3 capability audits. Click <strong>Verify Connection (Fast)</strong> to test reachability and credential listings instantly, or click <strong>Run Full Capability Audit (Deep)</strong> to run comprehensive read, write, and deletion tests on a bucket.
          </p>

          <!-- Grouped Table Checklists -->
          <div class="diagnostic-tables-container mt-24 flex-column gap-24">
            
            <!-- Category 1: Connection & Endpoint Diagnostics -->
            <div class="diagnostic-group-block border rounded bg-panel">
              <div class="diagnostic-group-header">
                <h4 class="margin-0 text-accent font-bold" style="font-size: 14px;">1. Connection & Endpoint Diagnostics</h4>
                <p class="margin-0 text-muted mt-4 text-xs">Validates client initialization, SSL rules, and DNS resolution of the configured endpoint URL.</p>
              </div>
              <div class="table-responsive">
                <table class="diagnostic-table w-full">
                  <thead>
                    <tr>
                      <th style="width: 35%">Feature / Capability</th>
                      <th style="width: 15%">Status</th>
                      <th style="width: 50%">Diagnostic Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="check in connectionChecks" :key="check.name" :class="check.status">
                      <td>
                        <div class="feature-cell">
                          <span class="feature-name">{{ check.name }}</span>
                          <span class="feature-desc">{{ getFeatureDescription(check.name) }}</span>
                        </div>
                      </td>
                      <td>
                        <span class="diagnostic-status-badge" :class="check.status">
                          {{ check.status === 'not_run' ? 'UNVERIFIED' : check.status.toUpperCase() }}
                        </span>
                      </td>
                      <td>
                        <code class="diagnostic-details-code">
                          {{ check.message || 'No details available.' }}
                        </code>
                      </td>
                    </tr>
                    <tr v-if="!connectionChecks.length">
                      <td colspan="3" class="text-center text-muted italic p-16 font-xs">No connection diagnostics configured.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Category 2: Bucket Operations Audit -->
            <div class="diagnostic-group-block border rounded bg-panel">
              <div class="diagnostic-group-header">
                <h4 class="margin-0 text-accent font-bold" style="font-size: 14px;">2. Bucket Operations Audit</h4>
                <p class="margin-0 text-muted mt-4 text-xs">Checks authorization policies for high-level bucket discovery and listing permissions.</p>
              </div>
              <div class="table-responsive">
                <table class="diagnostic-table w-full">
                  <thead>
                    <tr>
                      <th style="width: 35%">Feature / Capability</th>
                      <th style="width: 15%">Status</th>
                      <th style="width: 50%">Diagnostic Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="check in bucketChecks" :key="check.name" :class="check.status">
                      <td>
                        <div class="feature-cell">
                          <span class="feature-name">{{ check.name }}</span>
                          <span class="feature-desc">{{ getFeatureDescription(check.name) }}</span>
                        </div>
                      </td>
                      <td>
                        <span class="diagnostic-status-badge" :class="check.status">
                          {{ check.status === 'not_run' ? 'UNVERIFIED' : check.status.toUpperCase() }}
                        </span>
                      </td>
                      <td>
                        <code class="diagnostic-details-code">
                          {{ check.message || 'No details available.' }}
                        </code>
                      </td>
                    </tr>
                    <tr v-if="!bucketChecks.length">
                      <td colspan="3" class="text-center text-muted italic p-16 font-xs">No bucket diagnostics configured.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Category 3: Object Operations Audit -->
            <div class="diagnostic-group-block border rounded bg-panel">
              <div class="diagnostic-group-header">
                <h4 class="margin-0 text-accent font-bold" style="font-size: 14px;">3. Object Operations Audit</h4>
                <p class="margin-0 text-muted mt-4 text-xs">Validates S3 operations (list, write, delete) by performing a safe write/delete diagnostic cycle on a bucket.</p>
              </div>
              <div class="table-responsive">
                <table class="diagnostic-table w-full">
                  <thead>
                    <tr>
                      <th style="width: 35%">Feature / Capability</th>
                      <th style="width: 15%">Status</th>
                      <th style="width: 50%">Diagnostic Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="check in objectChecks" :key="check.name" :class="check.status">
                      <td>
                        <div class="feature-cell">
                          <span class="feature-name">{{ check.name }}</span>
                          <span class="feature-desc">{{ getFeatureDescription(check.name) }}</span>
                        </div>
                      </td>
                      <td>
                        <span class="diagnostic-status-badge" :class="check.status">
                          {{ check.status === 'not_run' ? 'UNVERIFIED' : check.status.toUpperCase() }}
                        </span>
                      </td>
                      <td>
                        <code class="diagnostic-details-code">
                          {{ check.message || 'No details available.' }}
                        </code>
                      </td>
                    </tr>
                    <tr v-if="!objectChecks.length">
                      <td colspan="3" class="text-center text-muted italic p-16 font-xs">No object diagnostics configured.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        </article>
      </section>
    </template>
  </div>
</template>

<style scoped>
.provider-diagnostics-page {
  display: flex;
  flex-direction: column;
  padding: 0 0 40px 0;
}

.provider-diagnostics-header {
  margin-bottom: 24px;
}

/* Polished Table Diagnostics */
.diagnostic-tables-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.diagnostic-group-block {
  border: 1px solid var(--border);
  background: var(--panel);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.diagnostic-group-header {
  border-bottom: 1px solid var(--border);
  padding: 16px 20px;
  background: rgba(15, 23, 42, 0.01);
}

[data-theme="dark"] .diagnostic-group-header {
  background: rgba(255, 255, 255, 0.01);
}

.table-responsive {
  width: 100%;
  overflow-x: auto;
}

.diagnostic-table {
  border-collapse: collapse;
  width: 100%;
}

.diagnostic-table th {
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  padding: 12px 20px;
  border-bottom: 1px solid var(--border);
  background: rgba(15, 23, 42, 0.02);
}

[data-theme="dark"] .diagnostic-table th {
  background: rgba(255, 255, 255, 0.02);
}

.diagnostic-table td {
  padding: 14px 20px;
  vertical-align: top;
  border-bottom: 1px solid var(--border);
}

.diagnostic-table tr:last-child td {
  border-bottom: none;
}

.diagnostic-table tr:hover {
  background: rgba(15, 23, 42, 0.01);
}

[data-theme="dark"] .diagnostic-table tr:hover {
  background: rgba(255, 255, 255, 0.01);
}

.feature-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 320px;
}

.feature-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.feature-desc {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.4;
}

.diagnostic-status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 3px 8px;
  border-radius: 4px;
  text-transform: uppercase;
  white-space: nowrap;
}

.diagnostic-status-badge.healthy {
  background: rgba(34, 197, 94, 0.08);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.15);
}

.diagnostic-status-badge.unhealthy {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.15);
}

.diagnostic-status-badge.warning {
  background: rgba(245, 158, 11, 0.08);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.15);
}

.diagnostic-status-badge.skipped {
  background: rgba(15, 23, 42, 0.05);
  color: var(--text-muted);
  border: 1px solid var(--border);
}

[data-theme="dark"] .diagnostic-status-badge.skipped {
  background: rgba(255, 255, 255, 0.05);
}

.diagnostic-status-badge.not_run {
  background: rgba(15, 23, 42, 0.03);
  color: var(--text-muted);
  border: 1px solid var(--border);
  opacity: 0.8;
}

[data-theme="dark"] .diagnostic-status-badge.not_run {
  background: rgba(255, 255, 255, 0.03);
}

.diagnostic-table tr.unhealthy td {
  background: rgba(239, 68, 68, 0.01);
}

.diagnostic-table tr.unhealthy .feature-name {
  color: #ef4444;
}

.diagnostic-details-code {
  font-family: var(--font-mono);
  font-size: 11px;
  line-height: 1.5;
  background: rgba(15, 23, 42, 0.03);
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  display: block;
  width: 100%;
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--text);
}

[data-theme="dark"] .diagnostic-details-code {
  background: rgba(255, 255, 255, 0.03);
}

.section-intro-text {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
}

.spin-loader {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.bg-danger-soft {
  background: rgba(239, 68, 68, 0.05);
  border-color: rgba(239, 68, 68, 0.15) !important;
}

.flex-center-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.flex-center-left {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}
</style>