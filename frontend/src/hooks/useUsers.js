import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api'

export function useMyProfile() {
  return useQuery({
    queryKey: ['users', 'me'],
    queryFn: async () => (await api.get('/api/condo/users/me')).data.data,
  })
}

export function useUsers(role) {
  return useQuery({
    queryKey: ['users', role || 'all'],
    queryFn: async () => {
      const params = role ? { role } : {}
      const res = await api.get('/api/condo/users', { params })
      return res.data.data
    },
  })
}

function useInvalidateUsers() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: ['users'] })
}

export function useCreateUser() {
  const invalidate = useInvalidateUsers()
  return useMutation({
    mutationFn: (payload) => api.post('/api/condo/users', payload),
    onSuccess: invalidate,
  })
}

export function useUpdateUser() {
  const invalidate = useInvalidateUsers()
  return useMutation({
    mutationFn: ({ id, ...payload }) => api.patch(`/api/condo/users/${id}`, payload),
    onSuccess: invalidate,
  })
}

export function useActivateUser() {
  const invalidate = useInvalidateUsers()
  return useMutation({
    mutationFn: (id) => api.post(`/api/condo/users/${id}/activate`),
    onSuccess: invalidate,
  })
}

export function useDeactivateUser() {
  const invalidate = useInvalidateUsers()
  return useMutation({
    mutationFn: (id) => api.post(`/api/condo/users/${id}/deactivate`),
    onSuccess: invalidate,
  })
}

export function useDeleteUser() {
  const invalidate = useInvalidateUsers()
  return useMutation({
    mutationFn: (id) => api.delete(`/api/condo/users/${id}`),
    onSuccess: invalidate,
  })
}
