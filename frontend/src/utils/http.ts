import axios from 'axios'

const base = import.meta.env.VITE_API_BASE?.replace(/\/$/, '') ?? ''

export const http = axios.create({
  baseURL: base,
  timeout: 120_000,
})

http.interceptors.response.use(
  (r) => r,
  (err) => Promise.reject(err),
)
