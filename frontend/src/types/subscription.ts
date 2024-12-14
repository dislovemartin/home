export type SubscriptionTier = 'free' | 'pro' | 'enterprise';

export interface SubscriptionFeatures {
    model_limit: number;
    requests_per_day: number;
    support: 'community' | 'email' | 'dedicated';
    features: string[];
}

export interface Subscription {
    id: string;
    name: string;
    tier: SubscriptionTier;
    price_monthly: number;
    price_yearly: number;
    features: SubscriptionFeatures;
    created_at: string;
    updated_at: string;
}

export interface UserSubscription {
    id: string;
    user_id: string;
    subscription_id: string;
    starts_at: string;
    ends_at: string | null;
    is_active: boolean;
    payment_status: string | null;
    created_at: string;
    updated_at: string;
}

export interface SubscriptionResponse {
    subscriptions: Subscription[];
}

export interface UserSubscriptionResponse {
    subscription: UserSubscription | null;
} 