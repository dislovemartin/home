use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::PgPool;
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize)]
pub struct PaymentIntent {
    pub id: Uuid,
    pub stripe_payment_intent_id: String,
    pub user_id: Uuid,
    pub subscription_id: Uuid,
    pub amount: f64,
    pub currency: String,
    pub status: String,
    pub client_secret: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PaymentMethod {
    pub id: Uuid,
    pub user_id: Uuid,
    pub stripe_payment_method_id: String,
    pub card_brand: Option<String>,
    pub card_last4: Option<String>,
    pub card_exp_month: Option<i32>,
    pub card_exp_year: Option<i32>,
    pub is_default: bool,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PaymentHistory {
    pub id: Uuid,
    pub user_id: Uuid,
    pub subscription_id: Uuid,
    pub payment_intent_id: Uuid,
    pub amount: f64,
    pub currency: String,
    pub status: String,
    pub created_at: DateTime<Utc>,
}

impl PaymentIntent {
    pub async fn create(
        pool: &PgPool,
        user_id: Uuid,
        subscription_id: Uuid,
        stripe_payment_intent_id: String,
        amount: f64,
        client_secret: String,
    ) -> Result<Self, sqlx::Error> {
        sqlx::query_as!(
            PaymentIntent,
            r#"
            INSERT INTO payment_intents (
                user_id, subscription_id, stripe_payment_intent_id,
                amount, status, client_secret
            )
            VALUES ($1, $2, $3, $4, 'pending', $5)
            RETURNING id, stripe_payment_intent_id, user_id, subscription_id,
                      amount, currency, status, client_secret, created_at, updated_at
            "#,
            user_id,
            subscription_id,
            stripe_payment_intent_id,
            amount,
            client_secret,
        )
        .fetch_one(pool)
        .await
    }

    pub async fn update_status(
        pool: &PgPool,
        stripe_payment_intent_id: &str,
        status: &str,
    ) -> Result<(), sqlx::Error> {
        sqlx::query!(
            r#"
            UPDATE payment_intents
            SET status = $1, updated_at = NOW()
            WHERE stripe_payment_intent_id = $2
            "#,
            status,
            stripe_payment_intent_id,
        )
        .execute(pool)
        .await?;
        Ok(())
    }

    pub async fn get_by_stripe_id(
        pool: &PgPool,
        stripe_payment_intent_id: &str,
    ) -> Result<Option<Self>, sqlx::Error> {
        sqlx::query_as!(
            PaymentIntent,
            r#"
            SELECT id, stripe_payment_intent_id, user_id, subscription_id,
                   amount, currency, status, client_secret, created_at, updated_at
            FROM payment_intents
            WHERE stripe_payment_intent_id = $1
            "#,
            stripe_payment_intent_id,
        )
        .fetch_optional(pool)
        .await
    }
}

impl PaymentMethod {
    pub async fn create(
        pool: &PgPool,
        user_id: Uuid,
        stripe_payment_method_id: String,
        card_details: Option<CardDetails>,
    ) -> Result<Self, sqlx::Error> {
        sqlx::query_as!(
            PaymentMethod,
            r#"
            INSERT INTO payment_methods (
                user_id, stripe_payment_method_id, card_brand,
                card_last4, card_exp_month, card_exp_year
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, user_id, stripe_payment_method_id, card_brand,
                      card_last4, card_exp_month, card_exp_year,
                      is_default, created_at, updated_at
            "#,
            user_id,
            stripe_payment_method_id,
            card_details.as_ref().map(|c| &c.brand),
            card_details.as_ref().map(|c| &c.last4),
            card_details.as_ref().map(|c| c.exp_month),
            card_details.as_ref().map(|c| c.exp_year),
        )
        .fetch_one(pool)
        .await
    }

    pub async fn get_default_for_user(
        pool: &PgPool,
        user_id: Uuid,
    ) -> Result<Option<Self>, sqlx::Error> {
        sqlx::query_as!(
            PaymentMethod,
            r#"
            SELECT id, user_id, stripe_payment_method_id, card_brand,
                   card_last4, card_exp_month, card_exp_year,
                   is_default, created_at, updated_at
            FROM payment_methods
            WHERE user_id = $1 AND is_default = true
            "#,
            user_id,
        )
        .fetch_optional(pool)
        .await
    }
}

impl PaymentHistory {
    pub async fn create(
        pool: &PgPool,
        user_id: Uuid,
        subscription_id: Uuid,
        payment_intent_id: Uuid,
        amount: f64,
        status: &str,
    ) -> Result<Self, sqlx::Error> {
        sqlx::query_as!(
            PaymentHistory,
            r#"
            INSERT INTO payment_history (
                user_id, subscription_id, payment_intent_id,
                amount, status
            )
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, user_id, subscription_id, payment_intent_id,
                      amount, currency, status, created_at
            "#,
            user_id,
            subscription_id,
            payment_intent_id,
            amount,
            status,
        )
        .fetch_one(pool)
        .await
    }

    pub async fn get_for_user(
        pool: &PgPool,
        user_id: Uuid,
        limit: i64,
    ) -> Result<Vec<Self>, sqlx::Error> {
        sqlx::query_as!(
            PaymentHistory,
            r#"
            SELECT id, user_id, subscription_id, payment_intent_id,
                   amount, currency, status, created_at
            FROM payment_history
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            "#,
            user_id,
            limit,
        )
        .fetch_all(pool)
        .await
    }
}

#[derive(Debug)]
pub struct CardDetails {
    pub brand: String,
    pub last4: String,
    pub exp_month: i32,
    pub exp_year: i32,
} 