use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    Json,
};
use uuid::Uuid;

use crate::{
    db::AIModelRepository,
    models::{AIModel, CreateAIModel, UpdateAIModel, ModelList, ListQueryParams},
};

#[axum::debug_handler]
pub async fn create_model(
    State(repo): State<AIModelRepository>,
    Json(model): Json<CreateAIModel>,
) -> Result<Json<AIModel>, StatusCode> {
    match repo.create(model).await {
        Ok(model) => Ok(Json(model)),
        Err(e) => {
            eprintln!("Failed to create model: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

#[axum::debug_handler]
pub async fn get_model(
    State(repo): State<AIModelRepository>,
    Path(id): Path<Uuid>,
) -> Result<Json<AIModel>, StatusCode> {
    match repo.get(id).await {
        Ok(Some(model)) => Ok(Json(model)),
        Ok(None) => Err(StatusCode::NOT_FOUND),
        Err(e) => {
            eprintln!("Failed to get model: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

#[axum::debug_handler]
pub async fn list_models(
    State(repo): State<AIModelRepository>,
    Query(params): Query<ListQueryParams>,
) -> Result<Json<ModelList>, StatusCode> {
    match repo.list(&params).await {
        Ok((models, total)) => {
            let page = params.page.unwrap_or(1);
            let per_page = params.per_page.unwrap_or(10);
            Ok(Json(ModelList {
                models,
                total,
                page,
                per_page,
            }))
        }
        Err(e) => {
            eprintln!("Failed to list models: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

#[axum::debug_handler]
pub async fn update_model(
    State(repo): State<AIModelRepository>,
    Path(id): Path<Uuid>,
    Json(model): Json<UpdateAIModel>,
) -> Result<Json<AIModel>, StatusCode> {
    match repo.update(id, model).await {
        Ok(Some(model)) => Ok(Json(model)),
        Ok(None) => Err(StatusCode::NOT_FOUND),
        Err(e) => {
            eprintln!("Failed to update model: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

#[axum::debug_handler]
pub async fn delete_model(
    State(repo): State<AIModelRepository>,
    Path(id): Path<Uuid>,
) -> Result<StatusCode, StatusCode> {
    match repo.delete(id).await {
        Ok(true) => Ok(StatusCode::NO_CONTENT),
        Ok(false) => Err(StatusCode::NOT_FOUND),
        Err(e) => {
            eprintln!("Failed to delete model: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

#[axum::debug_handler]
pub async fn increment_downloads(
    State(repo): State<AIModelRepository>,
    Path(id): Path<Uuid>,
) -> Result<StatusCode, StatusCode> {
    match repo.increment_downloads(id).await {
        Ok(_) => Ok(StatusCode::OK),
        Err(e) => {
            eprintln!("Failed to increment downloads: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
} 