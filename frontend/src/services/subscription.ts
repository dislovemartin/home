import axios from 'axios';
import type {
    Subscription,
    SubscriptionResponse,
    UserSubscription,
    UserSubscriptionResponse,
} from '../types/subscription';

const API_BASE = '/api';

export const subscriptionService = {
    async listSubscriptions(): Promise<Subscription[]> {
        const response = await axios.get<SubscriptionResponse>(`${API_BASE}/subscriptions`);
        return response.data.subscriptions;
    },

    async getSubscription(id: string): Promise<Subscription> {
        const response = await axios.get<Subscription>(`${API_BASE}/subscriptions/${id}`);
        return response.data;
    },

    async getUserSubscription(): Promise<UserSubscription | null> {
        const response = await axios.get<UserSubscriptionResponse>(`${API_BASE}/subscriptions/user`);
        return response.data.subscription;
    },

    async createSubscription(subscriptionId: string): Promise<UserSubscription> {
        const response = await axios.post<UserSubscription>(`${API_BASE}/subscriptions/subscribe`, {
            subscription_id: subscriptionId,
        });
        return response.data;
    },

    async cancelSubscription(): Promise<void> {
        await axios.post(`${API_BASE}/subscriptions/cancel`);
    },
}; 