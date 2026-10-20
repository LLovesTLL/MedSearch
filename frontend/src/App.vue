<script setup lang="ts">
import HeaderSection from './components/HeaderSection.vue'
import SearchSection from './components/SearchSection.vue'
import LiteratureSection from './components/LiteratureSection.vue'
import SummarySection from './components/SummarySection.vue'
import Toast from './components/common/Toast.vue'
</script>

<template>
  <div class="page">
    <HeaderSection />
    <main class="page-main">
      <SearchSection />
      <LiteratureSection />
      <SummarySection />
    </main>
    <Toast />
  </div>
</template>