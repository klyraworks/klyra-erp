// frontend/utils/api.js
export const getApiUrl = () => {
  if (typeof window === 'undefined') return 'http://localhost:8000';

  const host = window.location.hostname;
  const port = 8000;

  // Desarrollo local con subdominios
  if (host.includes('.local')) {
    return `http://${host}:${port}`;
  }

  // Producción
  if (host.includes('.klyra.com')) {
    return `https://${host.replace(':3000', '')}`;
  }

  // Fallback localhost
  return 'http://localhost:8000';
};

export const API_URL = getApiUrl();