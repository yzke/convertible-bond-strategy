<template>
  <div class="loading-spinner">
    <el-icon class="is-loading" :size="size">
      <Loading />
    </el-icon>
    <span v-if="text" class="loading-text">{{ text }}</span>
  </div>
</template>

<script setup lang="ts">
import { Loading } from '@element-plus/icons-vue'

defineProps<{
  size?: number
  text?: string
}>()
</script>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #409eff;
}

.loading-text {
  margin-top: 16px;
  color: #666;
}
</style>

