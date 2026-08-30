import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api'

export function useMaintenanceRequests(statusFilter) {
  return useQuery({
    queryKey: ['maintenance-requests', statusFilter || 'all'],
    queryFn: async () => {
      const params = statusFilter ? { status: statusFilter } : {}
      const res = await api.get('/api/condo/maintenance-requests', { params })
      return res.data.data
    },
  })
}

export function useCreateMaintenanceRequest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload) => api.post('/api/condo/maintenance-requests', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance-requests'] })
    },
  })
}

export function useAssignMaintenanceRequest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, assigned_to }) =>
      api.post(`/api/condo/maintenance-requests/assign?id=${id}`, { assigned_to }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance-requests'] })
    },
  })
}

export function useUpdateMaintenanceStatus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status, reason }) =>
      api.post(`/api/condo/maintenance-requests/status?id=${id}`, { status, reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance-requests'] })
    },
  })
}

export function useDeleteMaintenanceRequest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id) => api.delete(`/api/condo/maintenance-requests/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance-requests'] })
    },
  })
}
