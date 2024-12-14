use serde::{Deserialize, Serialize};
use sqlx::types::JsonValue;
use uuid::Uuid;
use chrono::{DateTime, Utc};

#[derive(Debug, Serialize, Deserialize, sqlx::Type)]
#[sqlx(type_name = "subscription_tier", rename_all = "lowercase")]
pub enum SubscriptionTier {
    Free,
    Pro,
    Enterprise,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Subscription {
    pub id: Uuid,
    pub name: String,
    pub tier: SubscriptionTier,
    pub price_monthly: f64,
    pub price_yearly: f64,
    pub features: JsonValue,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UserSubscription {
    pub id: Uuid,
    pub user_id: Uuid,
    pub subscription_id: Uuid,
    pub starts_at: DateTime<Utc>,
    pub ends_at: Option<DateTime<Utc>>,
    pub is_active: bool,
    pub payment_status: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl Subscription {
    pub async fn get_all(pool: &sqlx::PgPool) -> Result<Vec<Subscription>, sqlx::Error> {
        sqlx::query_as!(
            Subscription,
            r#"
            SELECT id, name, tier as "tier: SubscriptionTier",
                   price_monthly, price_yearly, features,
                   created_at, updated_at
            FROM subscriptions
            ORDER BY price_monthly ASC
            "#
        )
        .fetch_all(pool)
        .await
    }

    pub async fn get_by_id(pool: &sqlx::PgPool, id: Uuid) -> Result<Option<Subscription>, sqlx::Error> {
        sqlx::query_as!(
            Subscription,
            r#"
            SELECT id, name, tier as "tier: SubscriptionTier",
                   price_monthly, price_yearly, features,
                   created_at, updated_at
            FROM subscriptions
            WHERE id = $1
            "#,
            id
        )
        .fetch_optional(pool)
        .await
    }
}

impl UserSubscription {
    pub async fn get_active_for_user(
        pool: &sqlx::PgPool,
        user_id: Uuid,
    ) -> Result<Option<UserSubscription>, sqlx::Error> {
        sqlx::query_as!(
            UserSubscription,
            r#"
            SELECT id, user_id, subscription_id, starts_at,
                   ends_at, is_active, payment_status,
                   created_at, updated_at
            FROM user_subscriptions
            WHERE user_id = $1 AND is_active = true
            ORDER BY created_at DESC
            LIMIT 1
            "#,
            user_id
        )
        .fetch_optional(pool)
        .await
    }

    pub async fn create(
        pool: &sqlx::PgPool,
        user_id: Uuid,
        subscription_id: Uuid,
    ) -> Result<UserSubscription, sqlx::Error> {
        sqlx::query_as!(
            UserSubscription,
            r#"
            INSERT INTO user_subscriptions (
                user_id, subscription_id, starts_at,
                is_active, payment_status
            )
            VALUES ($1, $2, NOW(), true, 'pending')
            RETURNING id, user_id, subscription_id, starts_at,
                      ends_at, is_active, payment_status,
                      created_at, updated_at
            "#,
            user_id,
            subscription_id
        )
        .fetch_one(pool)
        .await
    }

    pub async fn cancel(
        pool: &sqlx::PgPool,
        user_id: Uuid,
    ) -> Result<(), sqlx::Error> {
        sqlx::query!(
            r#"
            UPDATE user_subscriptions
            SET is_active = false,
                ends_at = NOW(),
                updated_at = NOW()
            WHERE user_id = $1 AND is_active = true
            "#,
            user_id
        )
        .execute(pool)
        .await?;
        Ok(())
    }
} 