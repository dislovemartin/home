use sqlx::PgPool;
use uuid::Uuid;
use anyhow::Result;
use serde_json::Value as JsonValue;

use crate::models::{AIModel, CreateAIModel, UpdateAIModel, ListQueryParams};

#[derive(Clone)]
pub struct AIModelRepository {
    pool: PgPool,
}

impl AIModelRepository {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    pub async fn create(&self, model: CreateAIModel) -> Result<AIModel, sqlx::Error> {
        let record = sqlx::query_as!(
            AIModel,
            r#"
            INSERT INTO ai_models (
                name, description, model_type, framework, version,
                metadata, repository_url, is_public, price, required_tier,
                tags, performance_metrics
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING *
            "#,
            model.name,
            model.description,
            model.model_type,
            model.framework,
            model.version,
            model.metadata.unwrap_or_else(|| JsonValue::Object(serde_json::Map::new())),
            model.repository_url,
            model.is_public.unwrap_or(true),
            model.price,
            model.required_tier.unwrap_or_default() as _,
            &model.tags.unwrap_or_default(),
            model.performance_metrics
        )
        .fetch_one(&self.pool)
        .await?;

        Ok(record)
    }

    pub async fn get(&self, id: Uuid) -> Result<Option<AIModel>, sqlx::Error> {
        let record = sqlx::query_as!(
            AIModel,
            "SELECT * FROM ai_models WHERE id = $1",
            id
        )
        .fetch_optional(&self.pool)
        .await?;

        Ok(record)
    }

    pub async fn list(&self, params: &ListQueryParams) -> Result<(Vec<AIModel>, i64), sqlx::Error> {
        let page = params.page.unwrap_or(1);
        let per_page = params.per_page.unwrap_or(10);
        let offset = (page - 1) * per_page;

        let records = sqlx::query_as!(
            AIModel,
            r#"
            SELECT * FROM ai_models
            WHERE ($1::text IS NULL OR model_type = $1)
            AND ($2::float8 IS NULL OR performance_metrics->>'accuracy' >= $2::text)
            AND ($3::subscription_tier IS NULL OR required_tier = $3)
            ORDER BY created_at DESC
            LIMIT $4 OFFSET $5
            "#,
            params.model_type,
            params.min_accuracy,
            params.required_tier as _,
            per_page,
            offset
        )
        .fetch_all(&self.pool)
        .await?;

        let total = sqlx::query_scalar!(
            r#"
            SELECT COUNT(*) FROM ai_models
            WHERE ($1::text IS NULL OR model_type = $1)
            AND ($2::float8 IS NULL OR performance_metrics->>'accuracy' >= $2::text)
            AND ($3::subscription_tier IS NULL OR required_tier = $3)
            "#,
            params.model_type,
            params.min_accuracy,
            params.required_tier as _
        )
        .fetch_one(&self.pool)
        .await?
        .unwrap_or(0);

        Ok((records, total))
    }

    pub async fn update(&self, id: Uuid, model: UpdateAIModel) -> Result<Option<AIModel>, sqlx::Error> {
        let record = sqlx::query_as!(
            AIModel,
            r#"
            UPDATE ai_models
            SET
                name = COALESCE($1, name),
                description = COALESCE($2, description),
                model_type = COALESCE($3, model_type),
                framework = COALESCE($4, framework),
                version = COALESCE($5, version),
                metadata = COALESCE($6, metadata),
                repository_url = COALESCE($7, repository_url),
                is_public = COALESCE($8, is_public),
                price = COALESCE($9, price),
                required_tier = COALESCE($10, required_tier),
                tags = COALESCE($11, tags),
                performance_metrics = COALESCE($12, performance_metrics),
                updated_at = NOW()
            WHERE id = $13
            RETURNING *
            "#,
            model.name,
            model.description,
            model.model_type,
            model.framework,
            model.version,
            model.metadata,
            model.repository_url,
            model.is_public,
            model.price,
            model.required_tier as _,
            &model.tags.unwrap_or_default(),
            model.performance_metrics,
            id
        )
        .fetch_optional(&self.pool)
        .await?;

        Ok(record)
    }

    pub async fn delete(&self, id: Uuid) -> Result<bool, sqlx::Error> {
        let result = sqlx::query!(
            "DELETE FROM ai_models WHERE id = $1",
            id
        )
        .execute(&self.pool)
        .await?;

        Ok(result.rows_affected() > 0)
    }

    pub async fn increment_downloads(&self, id: Uuid) -> Result<(), sqlx::Error> {
        sqlx::query!(
            r#"
            UPDATE ai_models
            SET download_count = download_count + 1
            WHERE id = $1
            "#,
            id
        )
        .execute(&self.pool)
        .await?;

        Ok(())
    }
} 