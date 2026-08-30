import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api'

export function useUnitResidents() {
  return useQuery({
    queryKey: ['unit-residents'],
    queryFn: async () => (await api.get('/api/condo/unit-residents')).data.data,
  })
}

export function useCreateAssignment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload) => api.post('/api/condo/unit-residents', payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['unit-residents'] }),
  })
}

export function useEndAssignment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id) => api.post(`/api/condo/unit-residents/end`, null, { params: { id } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['unit-residents'] }),
  })
}
