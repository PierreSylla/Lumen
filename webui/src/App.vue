<script setup>
import { computed, ref } from 'vue'
import NavRail from './components/NavRail.vue'
import PageHeader from './components/PageHeader.vue'
import GroupsPage from './pages/GroupsPage.vue'
import ScenesPage from './pages/ScenesPage.vue'
import StubPage from './pages/StubPage.vue'
import GroupEditorSheet from './components/GroupEditorSheet.vue'
import { store } from './store/index.js'

const page = ref('rooms')
const sheet = ref(null) // null | { type: 'group', kind, isNew, group }

function navigate(key) {
  page.value = key
  sheet.value = null // rail navigation closes any open sheet
}

function openEditGroup(group) {
  sheet.value = { type: 'group', kind: group.kind === 'zone' ? 'zone' : 'room', isNew: false, group }
}

function handleAdd() {
  if (page.value === 'rooms' || page.value === 'zones') {
    sheet.value = { type: 'group', kind: page.value === 'zones' ? 'zone' : 'room', isNew: true, group: null }
  }
  // Scene creation opens the scene editor sheet - not built in step 1.
}

function handleRefresh() {
  // No-op until step 2 wires a real bridge snapshot read.
}

function onClickLamp() {
  // Opens the lamp sheet (colour wheel) - built in step 3.
}

const candidates = computed(() => {
  if (!sheet.value) return []
  const seen = new Map()
  for (const g of store.roomGroups) {
    for (const l of g.lamps) {
      if (!seen.has(l.id)) {
        seen.set(l.id, {
          id: l.id,
          name: l.name,
          archetype: l.archetype,
          currentRoomName: g.kind === 'room' ? g.name : null,
        })
      }
    }
  }
  const memberIds = new Set(sheet.value.group?.lamps.map((l) => l.id) ?? [])
  return [...seen.values()].map((c) => ({ ...c, selected: memberIds.has(c.id) }))
})

function closeSheet() {
  sheet.value = null
}

function saveGroup() {
  // Sample-only for step 1: real create/update lands with the bridge write
  // path (rooms/zones CRUD).
  closeSheet()
}
</script>

<template>
  <div class="app-shell">
    <NavRail :page="page" :bridge-ok="store.bridgeOk" @navigate="navigate" />
    <div class="content">
      <PageHeader :page="page" @add="handleAdd" @refresh="handleRefresh" />
      <div class="scroll-area">
        <GroupsPage
          v-if="page === 'rooms'"
          :groups="store.roomGroups"
          @edit-group="openEditGroup"
          @click-lamp="onClickLamp"
        />
        <GroupsPage
          v-else-if="page === 'zones'"
          :groups="store.zoneGroups"
          @edit-group="openEditGroup"
          @click-lamp="onClickLamp"
        />
        <ScenesPage v-else-if="page === 'scenes'" :sections="store.sceneSections" />
        <StubPage v-else-if="page === 'sync'" note="Screen sync page lands in step 7." />
        <StubPage v-else-if="page === 'setup'" note="Setup page lands in steps 5-6." />
      </div>
    </div>

    <GroupEditorSheet
      v-if="sheet?.type === 'group'"
      :kind="sheet.kind"
      :is-new="sheet.isNew"
      :initial-name="sheet.group?.name ?? ''"
      :candidates="candidates"
      @save="saveGroup"
      @cancel="closeSheet"
    />
  </div>
</template>

<style scoped>
.app-shell {
  position: relative;
  width: 100vw;
  height: 100vh;
  display: flex;
  background: var(--app-bg);
  color: var(--ink);
  font-size: 13px;
  overflow: hidden;
}
.content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.scroll-area {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 12px 14px 20px;
}
</style>
