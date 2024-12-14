use axum::{
    extract::{Path, State},
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::{
    error::AppError,
    models::subscription::{Subscription, UserSubscription},
    AppState,
};

pub fn subscription_routes() -> Router<AppState> {
    Router::new()
        .route("/subscriptions", get(list_subscriptions))
        .route("/subscriptions/:id", get(get_subscription))
        .route("/subscriptions/user", get(get_user_subscription))
        .route("/subscriptions/subscribe", post(create_subscription))
        .route("/subscriptions/cancel", post(cancel_subscription))
}

#[derive(Debug, Serialize)]
struct SubscriptionResponse {
    subscriptions: Vec<Subscription>,
}

async fn list_subscriptions(
    State(state): State<AppState>,
) -> Result<Json<SubscriptionResponse>, AppError> {
    let subscriptions = Subscription::get_all(&state.pool).await?;
    Ok(Json(SubscriptionResponse { subscriptions }))
}

async fn get_subscription(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<Subscription>, AppError> {
    let subscription = Subscription::get_by_id(&state.pool, id)
        .await?
        .ok_or_else(|| AppError::NotFound("Subscription not found".into()))?;
    Ok(Json(subscription))
}

#[derive(Debug, Serialize)]
struct UserSubscriptionResponse {
    subscription: Option<UserSubscription>,
}

async fn get_user_subscription(
    State(state): State<AppState>,
    // TODO: Extract user_id from JWT token
    user_id: Uuid,
) -> Result<Json<UserSubscriptionResponse>, AppError> {
    let subscription = UserSubscription::get_active_for_user(&state.pool, user_id).await?;
    Ok(Json(UserSubscriptionResponse { subscription }))
}

#[derive(Debug, Deserialize)]
struct CreateSubscriptionRequest {
    subscription_id: Uuid,
}

async fn create_subscription(
    State(state): State<AppState>,
    // TODO: Extract user_id from JWT token
    user_id: Uuid,
    Json(request): Json<CreateSubscriptionRequest>,
) -> Result<Json<UserSubscription>, AppError> {
    // Verify subscription exists
    Subscription::get_by_id(&state.pool, request.subscription_id)
        .await?
        .ok_or_else(|| AppError::NotFound("Subscription not found".into()))?;

    // Create user subscription
    let subscription = UserSubscription::create(
        &state.pool,
        user_id,
        request.subscription_id,
    ).await?;

    Ok(Json(subscription))
}

async fn cancel_subscription(
    State(state): State<AppState>,
    // TODO: Extract user_id from JWT token
    user_id: Uuid,
) -> Result<(), AppError> {
    UserSubscription::cancel(&state.pool, user_id).await?;
    Ok(())
} 