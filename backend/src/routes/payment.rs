use axum::{
    extract::{Path, State},
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::{
    error::AppError,
    models::{
        payment::{PaymentHistory, PaymentIntent, PaymentMethod},
        subscription::Subscription,
    },
    services::stripe::{CreatePaymentIntentRequest, StripeService},
    AppState,
};

pub fn payment_routes() -> Router<AppState> {
    Router::new()
        .route("/payments/create-intent", post(create_payment_intent))
        .route("/payments/status/:id", get(get_payment_status))
        .route("/payments/methods", get(list_payment_methods))
        .route("/payments/methods/attach", post(attach_payment_method))
        .route("/payments/history", get(get_payment_history))
        .route("/payments/webhook", post(handle_webhook))
}

async fn create_payment_intent(
    State(state): State<AppState>,
    // TODO: Extract user_id from JWT token
    user_id: Uuid,
    Json(request): Json<CreatePaymentIntentRequest>,
) -> Result<Json<PaymentIntent>, AppError> {
    // Get subscription details
    let subscription = Subscription::get_by_id(&state.pool, request.subscription_id)
        .await?
        .ok_or_else(|| AppError::NotFound("Subscription not found".into()))?;

    // Create payment intent
    let payment_intent = state
        .stripe_service
        .create_payment_intent(user_id, &subscription)
        .await?;

    Ok(Json(payment_intent))
}

#[derive(Debug, Serialize)]
struct PaymentStatusResponse {
    payment_intent: PaymentIntent,
}

async fn get_payment_status(
    State(state): State<AppState>,
    Path(payment_intent_id): Path<String>,
) -> Result<Json<PaymentStatusResponse>, AppError> {
    let payment_intent = PaymentIntent::get_by_stripe_id(&state.pool, &payment_intent_id)
        .await?
        .ok_or_else(|| AppError::NotFound("Payment intent not found".into()))?;

    Ok(Json(PaymentStatusResponse { payment_intent }))
}

#[derive(Debug, Serialize)]
struct PaymentMethodsResponse {
    payment_methods: Vec<PaymentMethod>,
}

async fn list_payment_methods(
    State(state): State<AppState>,
    // TODO: Extract user_id from JWT token
    user_id: Uuid,
) -> Result<Json<PaymentMethodsResponse>, AppError> {
    let payment_method = PaymentMethod::get_default_for_user(&state.pool, user_id).await?;
    let payment_methods = payment_method.map(|m| vec![m]).unwrap_or_default();

    Ok(Json(PaymentMethodsResponse { payment_methods }))
}

#[derive(Debug, Deserialize)]
struct AttachPaymentMethodRequest {
    payment_method_id: String,
}

async fn attach_payment_method(
    State(state): State<AppState>,
    // TODO: Extract user_id from JWT token
    user_id: Uuid,
    Json(request): Json<AttachPaymentMethodRequest>,
) -> Result<Json<PaymentMethod>, AppError> {
    // Attach payment method in Stripe and save to database
    state
        .stripe_service
        .attach_payment_method(user_id, &request.payment_method_id)
        .await?;

    let payment_method = PaymentMethod::get_default_for_user(&state.pool, user_id)
        .await?
        .ok_or_else(|| AppError::NotFound("Payment method not found".into()))?;

    Ok(Json(payment_method))
}

#[derive(Debug, Serialize)]
struct PaymentHistoryResponse {
    payments: Vec<PaymentHistory>,
}

async fn get_payment_history(
    State(state): State<AppState>,
    // TODO: Extract user_id from JWT token
    user_id: Uuid,
) -> Result<Json<PaymentHistoryResponse>, AppError> {
    let payments = PaymentHistory::get_for_user(&state.pool, user_id, 10).await?;
    Ok(Json(PaymentHistoryResponse { payments }))
}

async fn handle_webhook(
    State(state): State<AppState>,
    headers: axum::http::HeaderMap,
    body: String,
) -> Result<(), AppError> {
    let signature = headers
        .get("Stripe-Signature")
        .ok_or_else(|| AppError::BadRequest("Missing Stripe signature".into()))?
        .to_str()
        .map_err(|_| AppError::BadRequest("Invalid Stripe signature".into()))?;

    state
        .stripe_service
        .handle_webhook(body.as_bytes(), signature)
        .await?;

    Ok(())
} 