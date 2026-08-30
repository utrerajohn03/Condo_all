import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api'

export function useBills(params = {}) {
  return useQuery({
    queryKey: ['bills', params],
    queryFn: async () => (await api.get('/api/condo/bills', { params })).data.data,
  })
}

export function useMyBills() {
  return useQuery({
    queryKey: ['bills', 'mine'],
    queryFn: async () => (await api.get('/api/condo/bills/mine')).data.data,
  })
}

export function useCreateBill() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload) => api.post('/api/condo/bills', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bills'] })
    },
  })
}

export function useUpdateBill() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...payload }) => api.patch(`/api/condo/bills/${id}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bills'] })
    },
  })
}
