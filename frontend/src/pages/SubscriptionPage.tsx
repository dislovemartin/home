import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Subscription, UserSubscription } from '../types/subscription';
import { subscriptionService } from '../services/subscription';
import { PlanCard } from '../components/subscription/PlanCard';

export const SubscriptionPage: React.FC = () => {
    const navigate = useNavigate();
    const [plans, setPlans] = useState<Subscription[]>([]);
    const [userSubscription, setUserSubscription] = useState<UserSubscription | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [plansData, userSubData] = await Promise.all([
                    subscriptionService.listSubscriptions(),
                    subscriptionService.getUserSubscription(),
                ]);
                setPlans(plansData);
                setUserSubscription(userSubData);
            } catch (err) {
                setError('Failed to load subscription data');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    const handleSelectPlan = async (plan: Subscription) => {
        try {
            if (userSubscription?.subscription_id === plan.id) {
                return;
            }

            // If user has an active subscription, cancel it first
            if (userSubscription?.is_active) {
                await subscriptionService.cancelSubscription();
            }

            // Create new subscription
            const newSubscription = await subscriptionService.createSubscription(plan.id);
            setUserSubscription(newSubscription);

            // Redirect to payment page for paid plans
            if (plan.tier !== 'free') {
                navigate('/payment', { state: { plan } });
            }
        } catch (err) {
            setError('Failed to update subscription');
            console.error(err);
        }
    };

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <div className="text-lg">Loading...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex h-screen items-center justify-center">
                <div className="text-red-500">{error}</div>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="mb-8 text-center">
                <h1 className="mb-2 text-3xl font-bold">Choose Your Plan</h1>
                <p className="text-gray-600">
                    Select the plan that best fits your needs. Upgrade or downgrade at any time.
                </p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {plans.map((plan) => (
                    <PlanCard
                        key={plan.id}
                        plan={plan}
                        isActive={userSubscription?.subscription_id === plan.id}
                        onSelect={handleSelectPlan}
                    />
                ))}
            </div>

            {userSubscription && (
                <div className="mt-8 text-center">
                    <p className="text-sm text-gray-600">
                        Your current plan will be active until{' '}
                        {new Date(userSubscription.ends_at || '').toLocaleDateString()}
                    </p>
                    <button
                        onClick={() => subscriptionService.cancelSubscription()}
                        className="mt-2 text-sm text-red-500 hover:text-red-600"
                    >
                        Cancel Subscription
                    </button>
                </div>
            )}
        </div>
    );
}; 