import { describe, it, expect, beforeEach } from 'vitest'
import { useMaintenanceFilterStore, useUnitFilterStore } from './useFilterStore'

describe('useMaintenanceFilterStore', () => {
  beforeEach(() => {
    useMaintenanceFilterStore.getState().reset()
  })

  it('starts with empty search/filter and the "all" tab', () => {
    const state = useMaintenanceFilterStore.getState()
    expect(state.search).toBe('')
    expect(state.statusFilter).toBe('')
    expect(state.activeTab).toBe('all')
  })

  it('updates search text without touching other fields', () => {
    useMaintenanceFilterStore.getState().setSearch('leaking faucet')
    useMaintenanceFilterStore.getState().setStatusFilter('assigned')
    const state = useMaintenanceFilterStore.getState()
    expect(state.search).toBe('leaking faucet')
    expect(state.statusFilter).toBe('assigned')
  })

  it('switches the active tab', () => {
    useMaintenanceFilterStore.getState().setActiveTab('completed')
    expect(useMaintenanceFilterStore.getState().activeTab).toBe('completed')
  })

  it('reset() clears everything back to defaults', () => {
    useMaintenanceFilterStore.getState().setSearch('x')
    useMaintenanceFilterStore.getState().setStatusFilter('completed')
    useMaintenanceFilterStore.getState().setActiveTab('completed')
    useMaintenanceFilterStore.getState().reset()
    const state = useMaintenanceFilterStore.getState()
    expect(state).toMatchObject({ search: '', statusFilter: '', activeTab: 'all' })
  })
})

describe('useUnitFilterStore', () => {
  beforeEach(() => {
    useUnitFilterStore.getState().reset()
  })

  it('defaults to the "all" status tab', () => {
    expect(useUnitFilterStore.getState().statusTab).toBe('all')
  })

  it('updates the status tab independently of search', () => {
    useUnitFilterStore.getState().setSearch('tower a')
    useUnitFilterStore.getState().setStatusTab('vacant')
    const state = useUnitFilterStore.getState()
    expect(state.search).toBe('tower a')
    expect(state.statusTab).toBe('vacant')
  })
})
