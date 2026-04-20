export function getApiBase() {
  if (typeof window !== 'undefined' && window.electronAPI?.getApiBase) {
    return window.electronAPI.getApiBase();
  }

  return '';
}

export function apiUrl(path) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const base = getApiBase();
  return base ? `${base}${normalizedPath}` : normalizedPath;
}
