-- Add subscription tiers
CREATE TYPE subscription_tier AS ENUM ('free', 'pro', 'enterprise');

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    tier subscription_tier NOT NULL,
    price_monthly DECIMAL(10,2) NOT NULL,
    price_yearly DECIMAL(10,2) NOT NULL,
    features JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add user subscriptions
CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id),
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT true,
    payment_status VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enhance AI models table with marketplace features
ALTER TABLE ai_models ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES users(id);
ALTER TABLE ai_models ADD COLUMN IF NOT EXISTS is_public BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE ai_models ADD COLUMN IF NOT EXISTS price DECIMAL(10,2);
ALTER TABLE ai_models ADD COLUMN IF NOT EXISTS required_tier subscription_tier NOT NULL DEFAULT 'free';
ALTER TABLE ai_models ADD COLUMN IF NOT EXISTS downloads INTEGER NOT NULL DEFAULT 0;
ALTER TABLE ai_models ADD COLUMN IF NOT EXISTS avg_rating DECIMAL(3,2);
ALTER TABLE ai_models ADD COLUMN IF NOT EXISTS tags TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE ai_models ADD COLUMN IF NOT EXISTS performance_metrics JSONB;

-- Add model usage tracking
CREATE TABLE model_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES ai_models(id),
    user_id UUID NOT NULL REFERENCES users(id),
    request_count INTEGER NOT NULL DEFAULT 1,
    compute_time_ms INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add model ratings and reviews
CREATE TABLE model_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES ai_models(id),
    user_id UUID NOT NULL REFERENCES users(id),
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(model_id, user_id)
);

-- Add indexes for performance
CREATE INDEX idx_model_tags ON ai_models USING gin(tags);
CREATE INDEX idx_model_required_tier ON ai_models(required_tier);
CREATE INDEX idx_model_downloads ON ai_models(downloads DESC);
CREATE INDEX idx_model_rating ON ai_models(avg_rating DESC);
CREATE INDEX idx_model_usage_date ON model_usage(created_at);
CREATE INDEX idx_user_subscriptions_active ON user_subscriptions(user_id) WHERE is_active = true; 