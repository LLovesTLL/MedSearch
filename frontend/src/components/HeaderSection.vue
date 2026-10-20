<template>
  <header class="site-header">
    <div class="header-glow" aria-hidden="true"></div>
    <div class="header-pattern" aria-hidden="true"></div>
    <div class="header-content">
      <div class="header-badge">
        <span class="badge-dot"></span>
        <span class="badge-text">PubMed · AI · E-utilities</span>
      </div>
      <h1 class="site-title">
        <span class="title-accent">Med</span><span>Search</span>
      </h1>
      <p class="site-name">MedSearch - PubMed医学文献AI查询系统</p>
    </div>
  </header>
</template>

<style scoped>
.site-header {
  position: relative;
  background: var(--color-foreground);
  color: #ffffff;
  padding: var(--space-8) var(--space-5) var(--space-8);
  overflow: hidden;
}

.header-glow {
  position: absolute;
  top: -120px;
  right: -80px;
  width: 280px;
  height: 280px;
  border-radius: 50%;
  background: radial-gradient(
    circle,
    rgba(0, 82, 255, 0.35) 0%,
    transparent 70%
  );
  filter: blur(60px);
  animation: glow-breathe 6s ease-in-out infinite;
}

.header-pattern {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, #ffffff 1px, transparent 1px);
  background-size: 32px 32px;
  opacity: 0.04;
}

.header-content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-3);
  max-width: 768px;
  margin: 0 auto;
  animation: header-enter var(--duration-entrance) var(--ease-out) both;
}

.header-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 5px 12px;
  border-radius: var(--radius-full);
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(8px);
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-accent-secondary);
  animation: dot-pulse 2s ease-in-out infinite;
}

.badge-text {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.75);
}

.site-title {
  font-size: 34px;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.2;
}

.title-accent {
  background: var(--gradient-accent);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.site-name {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.66);
  letter-spacing: 0.02em;
}

@keyframes glow-breathe {
  0%,
  100% {
    opacity: 0.7;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.08);
  }
}

@keyframes dot-pulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.35);
    opacity: 0.7;
  }
}

@keyframes header-enter {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (min-width: 600px) {
  .site-header {
    padding: var(--space-10) var(--space-6);
  }

  .site-title {
    font-size: 40px;
  }
}
</style>