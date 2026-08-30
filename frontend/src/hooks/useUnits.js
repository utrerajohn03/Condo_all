import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api'

export function useUnits() {
  return useQuery({
    queryKey: ['units'],
    queryFn: async () => {
      const res = await api.get('/api/condo/units')
      return res.data.data
    },
  })
}

export function useCreateUnit() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload) => api.post('/api/condo/units', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['units'] })
    },
  })
}

export function useMyUnits() {
  return useQuery({
    queryKey: ['units', 'mine'],
    queryFn: async () => (await api.get('/api/condo/units/mine')).data.data,
  })
}

export function useUpdateUnit() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...payload }) => api.patch(`/api/condo/units/${id}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['units'] })
    },
  })
}
