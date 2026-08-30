import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api'

export function usePayments(params = {}) {
  return useQuery({
    queryKey: ['payments', params],
    queryFn: async () => (await api.get('/api/condo/payments', { params })).data.data,
  })
}

export function useMyPayments() {
  return useQuery({
    queryKey: ['payments', 'mine'],
    queryFn: async () => (await api.get('/api/condo/payments/mine')).data.data,
  })
}

export function useCreatePayment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload) => api.post('/api/condo/payments', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments'] })
      queryClient.invalidateQueries({ queryKey: ['bills'] })
    },
  })
}
