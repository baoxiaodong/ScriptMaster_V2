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
export const createErrorMessage = (message) => {
  return {
    message: `<span class='error-icon'>❌</span> ${message}`,
    grouping: true,
    duration: 3000,
    customClass: 'friendly-error-message'
  };
};