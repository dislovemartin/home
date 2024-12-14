use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use serde_json::Value as JsonValue;

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct AIModel {
    pub id: i32,
    pub name: String,
    pub description: String,
    pub model_type: String,
    pub framework: String,
    pub version: String,
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub updated_at: chrono::DateTime<chrono::Utc>,
    #[serde(default)]
    pub metadata: JsonValue,
    pub repository_url: Option<String>,
    pub download_count: i32,
    pub is_public: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CreateAIModel {
    pub name: String,
    pub description: String,
    pub model_type: String,
    pub framework: String,
    pub version: String,
    pub metadata: Option<JsonValue>,
    pub repository_url: Option<String>,
    pub is_public: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UpdateAIModel {
    pub name: Option<String>,
    pub description: Option<String>,
    pub model_type: Option<String>,
    pub framework: Option<String>,
    pub version: Option<String>,
    pub metadata: Option<JsonValue>,
    pub repository_url: Option<String>,
    pub is_public: Option<bool>,
} 