<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import type {
  ProviderConnection,
  ProviderSettings,
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
  Calendar,
  Activity,
  HardDrive,
  Cloud,
  Globe,
  Upload,
  Info,
  Lock,
  Unlock,
  Copy,
  Check,
  MapPin,
  Sliders,
  EyeOff,
  Terminal,
  FileText,
  Key
} from "@lucide/vue";

const route = useRoute();
const api = useObjectLensApi();

const providerId = computed(() => String(route.params.providerId || ""));
const provider = ref<ProviderConnection | null>(null);
const status = ref<ProviderStatus | null>(null);
const settings = ref<ProviderSettings | null>(null);
const loading = ref(true);
const error = ref("");

// Clipboard copy state
const endpointCopied = ref(false);
function copyEndpoint() {
  if (!provider.value?.endpoint_url) return;
  navigator.clipboard.writeText(provider.value.endpoint_url);
  endpointCopied.value = true;
  setTimeout(() => {
    endpointCopied.value = false;
  }, 2000);
}

onMounted(async () => {
  try {
    provider.value = await api.providerConnection(providerId.value);
    status.value = await api.providerStatus(providerId.value);
    settings.value = await api.providerSettings(providerId.value);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load provider details.";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="provider-details-page-new">
    <!-- Breadcrumb Path -->
    <nav class="breadcrumb real-breadcrumb" aria-label="Provider details path">
      <NuxtLink to="/">Dashboard</NuxtLink>
      <span class="breadcrumb-separator">/</span>
      <NuxtLink to="/providers">Providers</NuxtLink>
      <span class="breadcrumb-separator">/</span>
      <NuxtLink :to="`/providers/${encodeURIComponent(providerId)}`">
        {{ provider?.name || providerId }}
      </NuxtLink>
      <span class="breadcrumb-separator">/</span>
      <span class="current">Details</span>
    </nav>

    <!-- Header Section -->
    <header class="page-title-section provider-details-header">
      <div class="header-text-block">
        <div class="title-with-icon-row flex-wrap gap-10">
          <Cloud v-if="provider?.type === 'aws'" :size="24" class="text-accent flex-shrink-0" />
          <Database v-else-if="provider?.type === 'ceph'" :size="24" class="text-accent flex-shrink-0" />
          <Server v-else :size="24" class="text-accent flex-shrink-0" />
          <h1>{{ provider?.name || providerId }}</h1>
          <span class="provider-type-badge">{{ provider?.type?.toUpperCase() || "S3" }}</span>
          <span class="provider-status-badge" :class="status?.status === 'healthy' ? 'healthy' : 'unhealthy'">
            <span class="status-dot-indicator" />
            <span>{{ status?.status === 'healthy' ? 'Healthy' : 'Offline' }}</span>
          </span>
        </div>
        <p class="subtitle mt-4">
          {{ provider?.description || "Technical connection parameters, SSL settings, and credential encryption status." }}
        </p>
      </div>
      <div class="header-actions flex-wrap gap-8">
        <NuxtLink
          class="btn btn-secondary flex-center gap-6"
          :to="`/providers/${encodeURIComponent(providerId)}/diagnostics`"
        >
          <Activity :size="14" />
          <span>Diagnostics Audit</span>
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
        <h3>Connection Verification Failed</h3>
        <p>ObjectLens could not verify details for this connection configuration.</p>
        <code class="error-log">{{ error }}</code>
      </div>
    </div>

    <!-- Active Details Body -->
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

      <!-- Grid of Modern Metrics Cards -->
      <section class="metrics-card-grid" aria-label="Provider properties summary">
        <!-- Metric 1: Provider Type -->
        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Connection Type</span>
            <div class="metric-avatar-icon tint-accent">
              <Server :size="15" class="text-accent" />
            </div>
          </div>
          <div class="metric-content">
            <strong>{{ provider?.display_name || "S3 Native" }}</strong>
            <span class="metric-trend">{{ provider?.type }}</span>
          </div>
          <p class="metric-caption">Underlying storage client architecture.</p>
        </article>

        <!-- Metric 2: Health Status -->
        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Status Check</span>
            <div class="metric-avatar-icon" :class="status?.status === 'healthy' ? 'tint-success' : 'tint-danger'">
              <component :is="status?.status === 'healthy' ? ShieldCheck : AlertCircle" :size="15" :class="status?.status === 'healthy' ? 'text-success' : 'text-danger'" />
            </div>
          </div>
          <div class="metric-content">
            <strong :class="status?.status === 'healthy' ? 'text-success' : 'text-danger'">
              {{ status?.status === 'healthy' ? 'Healthy' : 'Unhealthy' }}
            </strong>
            <span class="metric-trend" :class="status?.status === 'healthy' ? 'success' : 'danger'">Connected</span>
          </div>
          <p class="metric-caption text-ellipsis">{{ status?.message || "Check connection parameters." }}</p>
        </article>

        <!-- Metric 3: Buckets count -->
        <article class="metric-card">
          <div class="metric-header">
            <span class="metric-title">Discovered Buckets</span>
            <div class="metric-avatar-icon tint-warning">
              <FolderOpen :size="15" class="text-warning" />
            </div>
          </div>
          <div class="metric-content">
            <strong>{{ status?.visible_bucket_count ?? 0 }}</strong>
            <span class="metric-trend">visible</span>
          </div>
          <p class="metric-caption">Buckets accessible with active keys.</p>
        </article>
      </section>

      <!-- Manifest Grid -->
      <section class="provider-manifest-wrapper mt-32">
        <div class="manifest-card-grid">
          <!-- Connection Settings Panel -->
          <article class="dashboard-content-block">
            <div class="block-header border-bottom pb-12 mb-16">
              <div class="flex-center-left gap-10">
                <Globe :size="18" class="text-accent" />
                <h3 class="margin-0">Endpoint Parameters</h3>
              </div>
            </div>

            <dl class="settings-details-list">
              <div class="settings-field-row flex-column align-items-start gap-6 pb-12 border-bottom">
                <dt class="flex-center-left gap-6">
                  <Globe :size="13" />
                  <span>S3 API Endpoint URL</span>
                </dt>
                <dd class="w-full flex-center-between gap-10">
                  <code class="font-mono text-ellipsis w-full block bg-soft" :title="provider?.endpoint_url || 'AWS S3 Edge'">
                    {{ provider?.endpoint_url || "AWS Global Edge (s3.amazonaws.com)" }}
                  </code>
                  <button v-if="provider?.endpoint_url" class="btn btn-secondary btn-icon-sm" @click="copyEndpoint" type="button" title="Copy endpoint URL">
                    <component :is="endpointCopied ? Check : Copy" :size="12" :class="{ 'text-success': endpointCopied }" />
                  </button>
                </dd>
              </div>

              <div class="settings-field-row pb-12 border-bottom">
                <dt class="flex-center-left gap-6">
                  <MapPin :size="13" />
                  <span>Target Region</span>
                </dt>
                <dd><code>{{ provider?.region || "us-east-1" }}</code></dd>
              </div>

              <div class="settings-field-row pb-12 border-bottom">
                <dt class="flex-center-left gap-6">
                  <FolderOpen :size="13" />
                  <span>Default Bucket</span>
                </dt>
                <dd><code>{{ provider?.default_bucket || "None Configured" }}</code></dd>
              </div>

              <div class="settings-field-row">
                <dt class="flex-center-left gap-6">
                  <Lock :size="13" />
                  <span>SSL Certificate Verification</span>
                </dt>
                <dd class="flex-center-left gap-6">
                  <span class="status-indicator-badge" :class="provider?.verify_ssl ? 'active' : 'inactive'">
                    {{ provider?.verify_ssl ? "Strict/Verified" : "Bypassed" }}
                  </span>
                </dd>
              </div>
            </dl>

            <div v-if="provider?.tags?.length" class="tag-row mt-16 pt-16 border-top flex-wrap gap-6">
              <span v-for="tag in provider.tags" :key="tag" class="tag-pill">{{ tag }}</span>
            </div>
          </article>

          <!-- Safe settings & Security Audit Panel -->
          <article id="settings" class="dashboard-content-block setting-panel-card">
            <div class="block-header border-bottom pb-12 mb-16">
              <div class="flex-center-left gap-10">
                <ShieldCheck :size="18" class="text-success" />
                <h3 class="margin-0">Safe Settings & Access Audit</h3>
              </div>
            </div>

            <!-- Credentials lock explanation banner -->
            <div class="secrets-secure-banner mb-16">
              <div class="banner-icon-container">
                <Lock :size="16" class="text-success" />
              </div>
              <div class="banner-text">
                <h5>Keys Locked and Hidden</h5>
                <p>Connection secrets are kept strictly server-side and never sent to the browser clients.</p>
              </div>
            </div>

            <dl class="settings-details-list">
              <div class="settings-field-row pb-12 border-bottom">
                <dt class="flex-center-left gap-6">
                  <Terminal :size="13" />
                  <span>Configuration Source</span>
                </dt>
                <dd class="text-ellipsis"><code :title="settings?.config_source">{{ settings?.config_source || "Environment Variables" }}</code></dd>
              </div>

              <div class="settings-field-row pb-12 border-bottom">
                <dt class="flex-center-left gap-6">
                  <ShieldCheck :size="13" />
                  <span>Active Secrets State</span>
                </dt>
                <dd class="flex-center-left gap-6">
                  <span class="status-indicator-badge" :class="settings?.secrets_loaded ? 'active' : 'inactive'">
                    {{ settings?.secrets_loaded ? "ACTIVE / LOCKED" : "UNLOADED" }}
                  </span>
                </dd>
              </div>

              <div class="settings-field-row pb-12 border-bottom">
                <dt class="flex-center-left gap-6">
                  <Key class="text-muted" :size="13" style="transform: rotate(45deg);" />
                  <span>S3 Access Key ID</span>
                </dt>
                <dd><code>••••••••••••••••••••</code></dd>
              </div>

              <div class="settings-field-row pb-12 border-bottom">
                <dt class="flex-center-left gap-6">
                  <Key class="text-muted" :size="13" style="transform: rotate(45deg);" />
                  <span>S3 Secret Access Key</span>
                </dt>
                <dd><code>••••••••••••••••••••••••••••••••</code></dd>
              </div>

              <div class="settings-field-row">
                <dt class="flex-center-left gap-6">
                  <Sliders :size="13" />
                  <span>Modifiable via Console</span>
                </dt>
                <dd>
                  <span class="status-indicator-badge inactive">
                    {{ settings?.editable ? "Enabled" : "Protected / Read-Only" }}
                  </span>
                </dd>
              </div>
            </dl>
          </article>
        </div>
      </section>

    </template>
  </div>
</template>

<style scoped>
.provider-details-page-new {
  display: flex;
  flex-direction: column;
  padding: 0 0 40px 0;
}

.provider-details-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border);
  padding-bottom: 24px;
  margin-bottom: 32px;
}

.title-with-icon-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-with-icon-row h1 {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin: 0;
  color: var(--text);
}

.provider-type-badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  padding: 3px 8px;
  border-radius: 4px;
  background: rgba(15, 23, 42, 0.05);
  color: var(--text-muted);
  border: 1px solid var(--border);
}

[data-theme="dark"] .provider-type-badge {
  background: rgba(255, 255, 255, 0.05);
}

.provider-status-badge {
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 12px;
  gap: 6px;
  border: 1px solid var(--border);
}

.provider-status-badge.healthy {
  background: rgba(34, 197, 94, 0.05);
  color: #22c55e;
  border-color: rgba(34, 197, 94, 0.15);
}

.provider-status-badge.unhealthy {
  background: rgba(239, 68, 68, 0.05);
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.15);
}

.status-dot-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.provider-status-badge.healthy .status-dot-indicator {
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.6);
}

.provider-status-badge.unhealthy .status-dot-indicator {
  background: #ef4444;
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.6);
}

/* Header Actions with perfect padding and no compression */
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.header-actions .btn {
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 600;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 36px;
  transition: all 0.15s ease;
  white-space: nowrap;
}

/* Polished Metrics Cards Grid */
.metrics-card-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-top: 32px;
  margin-bottom: 32px; /* Generous separation gap to parameters card */
}

@media (max-width: 768px) {
  .metrics-card-grid {
    grid-template-columns: 1fr;
  }
}

.metric-card {
  border: 1px solid var(--border);
  background: var(--panel);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.01);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.metric-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
}

[data-theme="dark"] .metric-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.metric-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.metric-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.metric-content {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.metric-content strong {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.02em;
}

.metric-trend {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--bg);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.metric-trend.success {
  background: rgba(34, 197, 94, 0.08);
  color: #22c55e;
}

.metric-trend.danger {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
}

.metric-caption {
  font-size: 12px;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.4;
}

.metric-avatar-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
}

.tint-accent {
  background: rgba(23, 107, 135, 0.08);
}

.tint-success {
  background: rgba(34, 197, 94, 0.08);
}

.tint-danger {
  background: rgba(239, 68, 68, 0.08);
}

.tint-warning {
  background: rgba(245, 158, 11, 0.08);
}

.manifest-card-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 24px;
}

@media (max-width: 1024px) {
  .manifest-card-grid {
    grid-template-columns: 1fr;
  }
}

/* Polished Content Blocks */
.dashboard-content-block {
  border: 1px solid var(--border);
  background: var(--panel);
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.01);
  display: flex;
  flex-direction: column;
}

.block-header h3 {
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.01em;
}

/* Polished Settings & Properties Lists */
.settings-details-list {
  display: flex;
  flex-direction: column;
  margin: 0;
}

.settings-field-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 1px solid var(--border);
}

.settings-field-row:last-child {
  border-bottom: none;
}

.settings-field-row dt {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
}

.settings-field-row dd {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  text-align: right;
  word-break: break-all;
}

.settings-field-row dd code {
  font-family: var(--font-mono);
  font-size: 11px;
  background: rgba(15, 23, 42, 0.03);
  border: 1px solid var(--border);
  padding: 3px 8px;
  border-radius: 4px;
  color: var(--text);
}

[data-theme="dark"] .settings-field-row dd code {
  background: rgba(255, 255, 255, 0.03);
}

.settings-field-row.flex-column {
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.settings-field-row.flex-column dd {
  width: 100%;
  text-align: left;
}

.bg-soft {
  background: rgba(15, 23, 42, 0.03);
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-family: var(--font-mono);
  border: 1px solid var(--border);
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
  display: block;
  text-align: left;
}

[data-theme="dark"] .bg-soft {
  background: rgba(255, 255, 255, 0.03);
}

.btn-icon-sm {
  width: 32px;
  height: 32px;
  padding: 0;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--panel);
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  cursor: pointer;
  flex-shrink: 0;
}

.btn-icon-sm:hover {
  background: rgba(15, 23, 42, 0.02);
  color: var(--text);
  border-color: var(--text-muted);
}

[data-theme="dark"] .btn-icon-sm:hover {
  background: rgba(255, 255, 255, 0.02);
}

.tag-pill {
  display: inline-flex;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 500;
  border: 1px solid var(--border);
  background: rgba(15, 23, 42, 0.02);
  border-radius: 12px;
  color: var(--text-muted);
}

[data-theme="dark"] .tag-pill {
  background: rgba(255, 255, 255, 0.02);
}

.secrets-secure-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: rgba(34, 197, 94, 0.03);
  border: 1px solid rgba(34, 197, 94, 0.1);
  border-radius: 6px;
  padding: 12px 14px;
  margin-bottom: 20px;
}

.banner-icon-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(34, 197, 94, 0.06);
  flex-shrink: 0;
  margin-top: 1px;
}

.banner-text {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.banner-text h5 {
  font-size: 12px;
  font-weight: 700;
  color: #22c55e;
  margin: 0;
  letter-spacing: -0.01em;
}

.banner-text p {
  font-size: 11px;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.4;
}

.status-indicator-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 700;
  border-radius: 4px;
  text-transform: uppercase;
}

.status-indicator-badge.active {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.status-indicator-badge.inactive {
  background: var(--border);
  color: var(--text-muted);
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