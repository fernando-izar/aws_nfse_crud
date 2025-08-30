import axios from 'axios';

export const api = (baseURL: string, token?: string) => {
  const inst = axios.create({ baseURL });
  inst.interceptors.request.use((cfg) => {
    if (token) cfg.headers.Authorization = `Bearer ${token}`;
    return cfg;
  });
  return inst;
};
