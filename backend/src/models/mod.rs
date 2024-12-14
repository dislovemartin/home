mod ai_model;
mod payment;
mod subscription;

pub use ai_model::*;
pub use payment::*;
pub use subscription::*;

use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct ListQueryParams {
    pub model_type: Option<String>,
    pub min_accuracy: Option<f64>,
    pub required_tier: Option<String>,
    pub page: Option<i64>,
    pub per_page: Option<i64>,
}

#[derive(Debug, Serialize)]
pub struct ModelList {
    pub models: Vec<AIModel>,
    pub total: i64,
    pub page: i64,
    pub per_page: i64,
} 