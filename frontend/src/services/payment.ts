import { loadStripe, type PaymentMethod } from '@stripe/stripe-js';
import axios from 'axios';
import { STRIPE_PUBLIC_KEY } from '../config/stripe';
import type { PaymentIntent, StripeCardElement } from '../types/stripe';

const stripe = loadStripe(STRIPE_PUBLIC_KEY);
const API_BASE = '/api';

export const paymentService = {
    async createPaymentIntent(subscriptionId: string): Promise<PaymentIntent> {
        const response = await axios.post<PaymentIntent>(`${API_BASE}/payments/create-intent`, {
            subscription_id: subscriptionId,
        });
        return response.data;
    },

    async confirmPayment(clientSecret: string, paymentMethod: PaymentMethod): Promise<boolean> {
        const stripeInstance = await stripe;
        if (!stripeInstance) {
            throw new Error('Stripe not initialized');
        }

        const { error } = await stripeInstance.confirmCardPayment(clientSecret, {
            payment_method: paymentMethod.id,
        });

        if (error) {
            console.error('Payment failed:', error);
            throw error;
        }

        return true;
    },

    async createPaymentMethod(cardElement: StripeCardElement): Promise<PaymentMethod> {
        const stripeInstance = await stripe;
        if (!stripeInstance) {
            throw new Error('Stripe not initialized');
        }

        const { error, paymentMethod } = await stripeInstance.createPaymentMethod({
            type: 'card',
            card: cardElement,
        });

        if (error) {
            throw error;
        }

        if (!paymentMethod) {
            throw new Error('Failed to create payment method');
        }

        return paymentMethod;
    },

    async getPaymentStatus(paymentIntentId: string): Promise<PaymentIntent> {
        const response = await axios.get<PaymentIntent>(
            `${API_BASE}/payments/status/${paymentIntentId}`
        );
        return response.data;
    },
}; 