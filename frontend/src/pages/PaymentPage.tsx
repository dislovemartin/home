import {
    CardElement,
    Elements,
    useElements,
    useStripe,
} from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { STRIPE_PUBLIC_KEY } from '../config/stripe';
import { paymentService } from '../services/payment';
import type { Subscription } from '../types/subscription';

const stripePromise = loadStripe(STRIPE_PUBLIC_KEY);

const CARD_ELEMENT_OPTIONS = {
    style: {
        base: {
            fontSize: '16px',
            color: '#424770',
            '::placeholder': {
                color: '#aab7c4',
            },
        },
        invalid: {
            color: '#9e2146',
        },
    },
};

interface PaymentFormProps {
    plan: Subscription;
}

const PaymentForm: React.FC<PaymentFormProps> = ({ plan }) => {
    const stripe = useStripe();
    const elements = useElements();
    const navigate = useNavigate();
    const [error, setError] = useState<string | null>(null);
    const [processing, setProcessing] = useState(false);
    const [clientSecret, setClientSecret] = useState('');

    useEffect(() => {
        const initializePayment = async () => {
            try {
                const paymentIntent = await paymentService.createPaymentIntent(plan.id);
                setClientSecret(paymentIntent.client_secret);
            } catch (err) {
                setError('Failed to initialize payment');
                console.error(err);
            }
        };

        initializePayment();
    }, [plan.id]);

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();

        if (!stripe || !elements) {
            return;
        }

        setProcessing(true);
        setError(null);

        try {
            const cardElement = elements.getElement(CardElement);
            if (!cardElement) {
                throw new Error('Card element not found');
            }

            const paymentMethod = await paymentService.createPaymentMethod(cardElement);
            await paymentService.confirmPayment(clientSecret, paymentMethod);

            // Payment successful, redirect to success page
            navigate('/payment/success', { state: { plan } });
        } catch (err) {
            const error = err as Error;
            setError(error.message || 'Payment failed');
            console.error('Payment error:', error);
        } finally {
            setProcessing(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="max-w-md space-y-6">
            <div className="rounded-md border p-4">
                <CardElement options={CARD_ELEMENT_OPTIONS} />
            </div>

            {error && (
                <div className="rounded-md bg-red-50 p-4 text-sm text-red-500">
                    {error}
                </div>
            )}

            <button
                type="submit"
                disabled={!stripe || processing}
                className={`
                    w-full rounded-lg bg-blue-600 px-4 py-2 font-medium text-white
                    transition-colors hover:bg-blue-700 disabled:bg-gray-400
                `}
            >
                {processing ? 'Processing...' : `Pay $${plan.price_monthly}`}
            </button>
        </form>
    );
};

export const PaymentPage: React.FC = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const plan = location.state?.plan as Subscription | undefined;

    if (!plan) {
        navigate('/subscriptions');
        return null;
    }

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="mb-8">
                <h1 className="mb-2 text-3xl font-bold">Complete Your Purchase</h1>
                <p className="text-gray-600">
                    You're subscribing to the {plan.name} plan at ${plan.price_monthly}/month
                </p>
            </div>

            <div className="grid gap-8 md:grid-cols-2">
                <div>
                    <Elements stripe={stripePromise}>
                        <PaymentForm plan={plan} />
                    </Elements>
                </div>

                <div className="rounded-lg border p-6">
                    <h2 className="mb-4 text-xl font-semibold">Order Summary</h2>
                    <div className="space-y-2">
                        <div className="flex justify-between">
                            <span>{plan.name} Plan</span>
                            <span>${plan.price_monthly}/month</span>
                        </div>
                        <div className="flex justify-between border-t pt-2">
                            <span className="font-medium">Total</span>
                            <span className="font-medium">${plan.price_monthly}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}; 