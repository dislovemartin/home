import React from 'react';
import type { Subscription } from '../../types/subscription';

interface PlanCardProps {
    plan: Subscription;
    isActive?: boolean;
    onSelect: (plan: Subscription) => void;
}

export const PlanCard: React.FC<PlanCardProps> = ({ plan, isActive = false, onSelect }) => {
    const { name, price_monthly, price_yearly, features } = plan;

    return (
        <div
            className={`
                rounded-lg border p-6 shadow-sm transition-all
                ${isActive ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-blue-200'}
            `}
        >
            <div className="mb-4">
                <h3 className="text-xl font-bold">{name}</h3>
                <div className="mt-2">
                    <span className="text-3xl font-bold">${price_monthly}</span>
                    <span className="text-gray-500">/month</span>
                </div>
                <div className="text-sm text-gray-500">
                    ${price_yearly}/year (save {Math.round((1 - price_yearly / (price_monthly * 12)) * 100)}%)
                </div>
            </div>

            <div className="mb-6">
                <div className="mb-2 font-semibold">Includes:</div>
                <ul className="space-y-2">
                    <li>
                        <span className="font-medium">
                            {features.model_limit === -1 ? 'Unlimited' : features.model_limit} models
                        </span>
                    </li>
                    <li>
                        <span className="font-medium">
                            {features.requests_per_day === -1 ? 'Unlimited' : features.requests_per_day} requests/day
                        </span>
                    </li>
                    {features.features.map((feature, index) => (
                        <li key={index} className="flex items-start">
                            <svg
                                className="mr-2 h-5 w-5 text-green-500 flex-shrink-0"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M5 13l4 4L19 7"
                                />
                            </svg>
                            <span>{feature}</span>
                        </li>
                    ))}
                </ul>
            </div>

            <button
                onClick={() => onSelect(plan)}
                className={`
                    w-full rounded-lg px-4 py-2 font-medium transition-colors
                    ${
                        isActive
                            ? 'bg-blue-600 text-white hover:bg-blue-700'
                            : 'bg-blue-100 text-blue-600 hover:bg-blue-200'
                    }
                `}
            >
                {isActive ? 'Current Plan' : 'Select Plan'}
            </button>
        </div>
    );
}; 