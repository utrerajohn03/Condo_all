import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api'

export function useSuperadminOverview() {
  return useQuery({
    queryKey: ['superadmin', 'overview'],
    queryFn: async () => (await api.get('/api/superadmin/overview')).data.data,
  })
}

export function useOrganization() {
  return useQuery({
    queryKey: ['superadmin', 'organization'],
    queryFn: async () => (await api.get('/api/superadmin/organization')).data.data,
  })
}

export function useUpdateOrganization() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload) => api.patch('/api/superadmin/organization', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['superadmin', 'organization'] })
    },
  })
}

export function usePortalConfig() {
  return useQuery({
    queryKey: ['superadmin', 'portal-config'],
    queryFn: async () => (await api.get('/api/superadmin/portal-config')).data.data,
  })
}

export function useSetPortalConfig() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ key, setting_value }) =>
      api.put(`/api/superadmin/portal-config/${key}`, { setting_value }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['superadmin', 'portal-config'] })
    },
  })
}
