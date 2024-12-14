mod config;
mod db;
mod models;
mod routes;

use axum::{
    Router,
    routing::{get, post, put, delete},
};
use std::net::SocketAddr;
use std::env;
use std::error::Error;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() {
    // Load environment variables from .env file
    dotenvy::dotenv().ok();

    // Set up tracing
    tracing_subscriber::registry()
        .with(tracing_subscriber::fmt::layer())
        .init();

    // Print environment variables for debugging
    println!("Environment variables:");
    for (key, value) in env::vars() {
        println!("  {} = {}", key, value);
    }

    // Get command from args
    let args: Vec<String> = env::args().collect();
    let command = args.get(1).map(|s| s.as_str());

    println!("Creating database pool...");
    // Create database connection pool
    let pool = match config::create_pool().await {
        Ok(pool) => {
            println!("Database pool created successfully");
            pool
        }
        Err(e) => {
            eprintln!("Failed to create database pool: {}", e);
            std::process::exit(1);
        }
    };

    match command {
        Some("migrate") => {
            println!("Running migrations...");
            match sqlx::migrate!("./migrations").run(&pool).await {
                Ok(_) => {
                    println!("Migrations completed successfully!");
                }
                Err(e) => {
                    eprintln!("Failed to run migrations: {}", e);
                    if let Some(source) = e.source() {
                        eprintln!("Caused by: {}", source);
                    }
                    std::process::exit(1);
                }
            }
            return;
        }
        Some(cmd) => {
            eprintln!("Unknown command: {}", cmd);
            std::process::exit(1);
        }
        None => {
            // Run migrations before starting the server
            println!("Running migrations...");
            if let Err(e) = sqlx::migrate!("./migrations").run(&pool).await {
                eprintln!("Failed to run migrations: {}", e);
                if let Some(source) = e.source() {
                    eprintln!("Caused by: {}", source);
                }
                std::process::exit(1);
            }
            println!("Migrations completed successfully!");

            // Create AI model repository
            let repo = db::AIModelRepository::new(pool);

            // Build our application with routes
            let app = Router::new()
                .route("/api/health", get(|| async { "OK" }))
                .route("/api/models", post(routes::create_model))
                .route("/api/models", get(routes::list_models))
                .route("/api/models/:id", get(routes::get_model))
                .route("/api/models/:id", put(routes::update_model))
                .route("/api/models/:id", delete(routes::delete_model))
                .route("/api/models/:id/downloads", post(routes::increment_downloads))
                .with_state(repo);

            // Get host and port from environment variables or use defaults
            let host = env::var("HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
            let port = env::var("PORT")
                .ok()
                .and_then(|p| p.parse().ok())
                .unwrap_or(3000);

            // Create the address to bind to
            let addr: SocketAddr = format!("{}:{}", host, port)
                .parse()
                .expect("Failed to parse address");

            tracing::info!("listening on {}", addr);
            
            let listener = tokio::net::TcpListener::bind(addr)
                .await
                .expect("Failed to bind to address");

            println!("Server starting on {}", addr);
            
            match axum::serve(listener, app).await {
                Ok(_) => {
                    println!("Server shutdown gracefully");
                    std::process::exit(0);
                }
                Err(e) => {
                    eprintln!("Server error: {}", e);
                    std::process::exit(1);
                }
            }
        }
    }
}
