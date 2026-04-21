import { createApp } from 'vue';
import axios from 'axios';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import './style.css';
import App from './App.vue';
import { getApiBase } from './api/base';
import { getFriendlyErrorText } from './utils';

axios.defaults.baseURL = getApiBase();
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    error.friendlyMessage = getFriendlyErrorText(error, '请求失败，请检查后端服务或提示词配置');
    return Promise.reject(error);
  }
);

const app = createApp(App);
app.use(ElementPlus);
app.mount('#app');
