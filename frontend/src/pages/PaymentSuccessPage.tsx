import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import type { Subscription } from '../types/subscription';

export const PaymentSuccessPage: React.FC = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const plan = location.state?.plan as Subscription | undefined;

    if (!plan) {
        navigate('/subscriptions');
        return null;
    }

    return (
        <div className="container mx-auto flex min-h-[60vh] items-center justify-center px-4">
            <div className="text-center">
                <div className="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                    <svg
                        className="h-8 w-8 text-green-500"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                        />
                    </svg>
                </div>

                <h1 className="mb-2 text-3xl font-bold">Payment Successful!</h1>
                <p className="mb-8 text-gray-600">
                    Thank you for subscribing to the {plan.name} plan.
                    Your subscription is now active.
                </p>

                <div className="space-x-4">
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="rounded-lg bg-blue-600 px-6 py-2 font-medium text-white transition-colors hover:bg-blue-700"
                    >
                        Go to Dashboard
                    </button>
                    <button
                        onClick={() => navigate('/account/subscription')}
                        className="rounded-lg bg-gray-100 px-6 py-2 font-medium text-gray-600 transition-colors hover:bg-gray-200"
                    >
                        View Subscription
                    </button>
                </div>
            </div>
        </div>
    );
}; 