import { create } from 'zustand'

/**
 * zustand — client-side UI state for the list pages (search text, status/building
 * filters, active tab). Deliberately kept separate from react-query's server-state
 * cache: this store never holds data that came from the API, only what the user is
 * currently typing/selecting to filter that data.
 */
export const useMaintenanceFilterStore = create((set) => ({
  search: '',
  statusFilter: '',
  activeTab: 'all', // 'all' | 'completed' — mirrors the Utrera mockup's page tabs
  setSearch: (search) => set({ search }),
  setStatusFilter: (statusFilter) => set({ statusFilter }),
  setActiveTab: (activeTab) => set({ activeTab }),
  reset: () => set({ search: '', statusFilter: '', activeTab: 'all' }),
}))

export const useUnitFilterStore = create((set) => ({
  search: '',
  statusTab: 'all', // 'all' | 'occupied' | 'vacant' | 'under_maintenance'
  setSearch: (search) => set({ search }),
  setStatusTab: (statusTab) => set({ statusTab }),
  reset: () => set({ search: '', statusTab: 'all' }),
}))
