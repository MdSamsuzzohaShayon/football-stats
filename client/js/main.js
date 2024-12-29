// Base configuration class
class ApiConfig {
    static BASE_URL = 'http://localhost:8000/api';
    static ENDPOINTS = {
        TEAMS: '/teams',
        MATCHES: '/matches',
        PLAYERS: '/players'
    };
}

// Base API Service class
class ApiService {
    async fetchData(endpoint, options = {}) {
        try {
            const response = await fetch(`${ApiConfig.BASE_URL}${endpoint}`, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            NotificationService.show('error', `API Error: ${error.message}`);
            throw error;
        }
    }

    get(endpoint) { return this.fetchData(`${endpoint}?reaload=true`); }
    post(endpoint, data) { return this.fetchData(endpoint, { method: 'POST', body: JSON.stringify(data) }); }
    put(endpoint, data) { return this.fetchData(endpoint, { method: 'PUT', body: JSON.stringify(data) }); }
    delete(endpoint) { return this.fetchData(endpoint, { method: 'DELETE' }); }
}

// Notification Service class
class NotificationService {
    static show(type, message) {
        const toastHTML = `
            <div class="toast-container position-fixed bottom-0 end-0 p-3">
                <div class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : 'success'}" role="alert">
                    <div class="d-flex">
                        <div class="toast-body">${message}</div>
                        <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast"></button>
                    </div>
                </div>
            </div>`;

        document.body.insertAdjacentHTML('beforeend', toastHTML);
        const toastElement = document.querySelector('.toast:last-child');
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
    }
}


// Base Manager class
class BaseManager {
    constructor() {
        this.apiService = new ApiService();
        this.data = []; // Add base storage for entities
    }

    // Add generic CRUD operations
    async getAll(endpoint, renderCallback) {
        try {
            const data = await this.apiService.get(endpoint);
            this.data = data; // Store data for reuse
            if (renderCallback) renderCallback(data);
            return data;
        } catch (error) {
            this.handleError(error, 'fetch data');
        }
        return [];
    }

    async create(endpoint, data, successMessage = 'Created successfully') {
        try {
            await this.apiService.post(endpoint, data);
            NotificationService.show('success', successMessage);
            await this.refreshData();
        } catch (error) {
            this.handleError(error, 'create');
        }
    }

    async update(endpoint, id, data, successMessage = 'Updated successfully') {
        try {
            await this.apiService.put(`${endpoint}/${id}`, data);
            NotificationService.show('success', successMessage);
            await this.refreshData();
        } catch (error) {
            this.handleError(error, 'update');
        }
    }

    async delete(endpoint, id, successMessage = 'Deleted successfully') {
        try {
            await this.apiService.delete(`${endpoint}/${id}`);
            NotificationService.show('success', successMessage);
            await this.refreshData();
        } catch (error) {
            this.handleError(error, 'delete');
        }
    }

    // Add helper methods
    closeModal(modalId) {
        const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        if (modal) modal.hide();
    }

    handleError(error, context) {
        NotificationService.show('error', `Failed to ${context}: ${error.message}`);
        console.error(`Failed to ${context}:`, error);
    }
}


const MatchStatus = Object.freeze({
    NOT_STARTED: "not_started",
    RUNNING: "running",
    HALF_TIME: "half_time",
    FULL_TIME: "full_time"
});