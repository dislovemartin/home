-- Seed initial subscription tiers
INSERT INTO subscriptions (name, tier, price_monthly, price_yearly, features) VALUES
(
    'Free Tier',
    'free',
    0.00,
    0.00,
    '{
        "model_limit": 5,
        "requests_per_day": 100,
        "support": "community",
        "features": [
            "Access to public models",
            "Basic API access",
            "Community support"
        ]
    }'
),
(
    'Pro',
    'pro',
    29.99,
    299.99,
    '{
        "model_limit": 20,
        "requests_per_day": 1000,
        "support": "email",
        "features": [
            "Access to premium models",
            "Priority API access",
            "Email support",
            "Advanced analytics",
            "Custom model hosting"
        ]
    }'
),
(
    'Enterprise',
    'enterprise',
    199.99,
    1999.99,
    '{
        "model_limit": -1,
        "requests_per_day": -1,
        "support": "dedicated",
        "features": [
            "Unlimited model access",
            "Dedicated API endpoints",
            "24/7 priority support",
            "Custom model training",
            "SLA guarantees",
            "Team management",
            "SSO integration",
            "Audit logs"
        ]
    }'
); 