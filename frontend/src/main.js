import { createApp } from 'vue';
import axios from 'axios';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import './style.css';
import App from './App.vue';
import { getApiBase } from './api/base';

axios.defaults.baseURL = getApiBase();

const app = createApp(App);
app.use(ElementPlus);
app.mount('#app');
