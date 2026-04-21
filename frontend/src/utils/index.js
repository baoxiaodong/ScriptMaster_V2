/**
 * 公共工具函数
 */

/**
 * 节流函数，用于减少DOM操作频率
 * @param {Function} func - 要执行的函数
 * @param {number} delay - 延迟时间（毫秒）
 * @returns {Function} 节流后的函数
 */
export const throttle = (func, delay) => {
  let lastCall = 0;
  return function(...args) {
    const now = Date.now();
    if (now - lastCall < delay) return;
    lastCall = now;
    return func.apply(this, args);
  };
};

/**
 * 简单的加密函数，用于保护API密钥
 * @param {string} apiKey - API密钥
 * @returns {string} 加密后的API密钥
 */
export const encryptApiKey = (apiKey) => {
  if (!apiKey) return '';
  // 使用简单的Base64编码作为基本保护
  return btoa(unescape(encodeURIComponent(apiKey)));
};

/**
 * 解密函数
 * @param {string} encryptedKey - 加密后的API密钥
 * @returns {string} 解密后的API密钥
 */
export const decryptApiKey = (encryptedKey) => {
  if (!encryptedKey) return '';
  try {
    return decodeURIComponent(escape(atob(encryptedKey)));
  } catch {
    return '';
  }
};

/**
 * 检查是否在Mock模式下
 * @param {Object} config - 配置对象
 * @returns {boolean} 是否在Mock模式下
 */
export const isMockMode = (config) => {
  return config && config.provider === 'Mock (演示)';
};

/**
 * 生成友好的错误提示
 * @param {string} message - 错误信息
 * @returns {Object} 错误提示配置
 */
export const getFriendlyErrorText = (error, fallback = '操作失败，请稍后重试') => {
  if (typeof error === 'string' && error.trim()) return error.trim();

  const serverMessage = error?.response?.data?.message;
  if (typeof serverMessage === 'string' && serverMessage.trim()) return serverMessage.trim();

  const friendlyMessage = error?.friendlyMessage;
  if (typeof friendlyMessage === 'string' && friendlyMessage.trim()) return friendlyMessage.trim();

  return fallback;
};

export const createErrorMessage = (error, fallback = '操作失败，请稍后重试') => {
  const message = getFriendlyErrorText(error, fallback);
  return {
    message: `<span class='error-icon'>❌</span> ${message}`,
    grouping: true,
    duration: 3000,
    customClass: 'friendly-error-message'
  };
};

/**
 * 判断是否属于可短暂重试的启动期网络错误
 * @param {any} error - 请求异常
 * @returns {boolean}
 */
export const isRetriableNetworkError = (error) => {
  const message = String(error?.message || '');
  const code = String(error?.code || '');
  const status = error?.response?.status;

  return (
    !status ||
    status >= 500 ||
    code === 'ECONNREFUSED' ||
    code === 'ERR_NETWORK' ||
    message.includes('ECONNREFUSED') ||
    message.includes('Network Error') ||
    message.includes('Failed to fetch')
  );
};

/**
 * 带重试的异步请求，适合后端冷启动场景
 * @param {Function} task - 返回 Promise 的函数
 * @param {Object} options - 重试配置
 * @returns {Promise<any>}
 */
export const retryAsync = async (task, options = {}) => {
  const {
    retries = 3,
    delayMs = 600,
    shouldRetry = () => true,
  } = options;

  let lastError;
  for (let attempt = 0; attempt <= retries; attempt += 1) {
    try {
      return await task();
    } catch (error) {
      lastError = error;
      if (attempt >= retries || !shouldRetry(error, attempt)) {
        throw error;
      }
      await new Promise((resolve) => setTimeout(resolve, delayMs * (attempt + 1)));
    }
  }

  throw lastError;
};
