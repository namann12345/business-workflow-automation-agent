import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
});

// Generic agent request
export const runAgent = async (requestText, context = {}, file = null) => {
    const formData = new FormData();
    formData.append('request', requestText);
    formData.append('context', JSON.stringify(context));
    if (file) {
        formData.append('file', file);
    }

    const response = await api.post('/agent/run', formData);
    return response.data;
};

export const getWorkflows = async () => {
    const response = await api.get('/workflows');
    return response.data;
};

export const getExecutions = async (limit = 100) => {
    const response = await api.get(`/executions?limit=${limit}`);
    return response.data;
};
