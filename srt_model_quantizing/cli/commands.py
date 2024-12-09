"""Command-line interface commands."""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..catalog import ModelCatalog, ModelCatalogEntry
from ..config import config
from ..nemo import ModelOptimizer, OptimizationConfig
from ..versioning import ModelVersionManager

app = typer.Typer(help="SRT Model Quantizing CLI")
console = Console()

@app.command()
def serve(
    host: str = typer.Option(config.host, help="Server host"),
    port: int = typer.Option(config.port, help="Server port"),
    workers: int = typer.Option(config.workers, help="Number of worker processes"),
    reload: bool = typer.Option(config.reload, help="Enable auto-reload"),
    ssl_keyfile: Optional[str] = typer.Option(config.ssl_keyfile, help="SSL key file"),
    ssl_certfile: Optional[str] = typer.Option(config.ssl_certfile, help="SSL certificate file")
):
    """Start the server."""
    import uvicorn
    
    console.print("[bold green]Starting SRT Model Quantizing server...[/bold green]")
    
    uvicorn.run(
        "srt_model_quantizing.server:app",
        host=host,
        port=port,
        workers=workers,
        reload=reload,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile
    )

@app.command()
def optimize(
    model_name: str = typer.Argument(..., help="Name of the model to optimize"),
    precision: str = typer.Option("fp16", help="Target precision (fp32, fp16, int8, fp8)"),
    output_dir: Path = typer.Option(None, help="Output directory for optimized model"),
    use_transformer_engine: bool = typer.Option(True, help="Use Transformer Engine"),
    fp8_hybrid: bool = typer.Option(True, help="Use FP8 hybrid mode"),
    gradient_checkpointing: bool = typer.Option(True, help="Use gradient checkpointing"),
    max_batch_size: int = typer.Option(128, help="Maximum batch size")
):
    """Optimize a model using NeMo framework."""
    try:
        # Create optimization config
        opt_config = OptimizationConfig(
            precision=precision,
            use_transformer_engine=use_transformer_engine,
            fp8_hybrid=fp8_hybrid,
            gradient_checkpointing=gradient_checkpointing,
            max_batch_size=max_batch_size
        )
        
        # Initialize optimizer
        version_manager = ModelVersionManager(config.storage.model_repository)
        model_path = version_manager.get_version_path(model_name)
        optimizer = ModelOptimizer(model_path, opt_config)
        
        # Set output path
        if output_dir is None:
            output_dir = config.storage.model_repository / model_name / "optimized"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Optimize model
        console.print(f"[bold]Optimizing model {model_name}...[/bold]")
        optimized_path = optimizer.optimize(output_dir)
        
        # Add new version
        version = version_manager.add_version(
            model_name=model_name,
            model_path=optimized_path,
            metadata={"optimization_config": opt_config.dict()}
        )
        
        console.print(f"[bold green]Model optimized successfully![/bold green]")
        console.print(f"New version: {version.version}")
        console.print(f"Output path: {optimized_path}")
        
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        raise typer.Exit(1)

@app.command()
def list_models(
    framework: Optional[str] = typer.Option(None, help="Filter by framework"),
    task: Optional[str] = typer.Option(None, help="Filter by task"),
    precision: Optional[str] = typer.Option(None, help="Filter by precision"),
    tags: Optional[str] = typer.Option(None, help="Filter by tags (comma-separated)")
):
    """List models in the catalog."""
    try:
        catalog = ModelCatalog(config.storage.catalog_path)
        
        # Parse tags
        tag_set = set(tags.split(",")) if tags else None
        
        # Get models
        models = catalog.list_models(
            framework=framework,
            task=task,
            precision=precision,
            tags=tag_set
        )
        
        # Create table
        table = Table(title="Model Catalog")
        table.add_column("Name")
        table.add_column("Version")
        table.add_column("Framework")
        table.add_column("Task")
        table.add_column("Precision")
        table.add_column("Tags")
        
        for model in models:
            table.add_row(
                model.metadata.name,
                model.metadata.version,
                model.metadata.framework.value,
                model.metadata.task.value,
                model.metadata.precision.value,
                ", ".join(model.metadata.tags)
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        raise typer.Exit(1)

@app.command()
def show_model(
    name: str = typer.Argument(..., help="Model name"),
    version: str = typer.Argument(..., help="Model version")
):
    """Show details of a specific model."""
    try:
        catalog = ModelCatalog(config.storage.catalog_path)
        model = catalog.get_model(name, version)
        
        if not model:
            console.print(f"[bold red]Model {name}:{version} not found[/bold red]")
            raise typer.Exit(1)
        
        console.print(json.dumps(model.dict(), indent=2))
        
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        raise typer.Exit(1)

@app.command()
def delete_model(
    name: str = typer.Argument(..., help="Model name"),
    version: str = typer.Argument(..., help="Model version"),
    force: bool = typer.Option(False, "--force", "-f", help="Force deletion without confirmation")
):
    """Delete a model from the catalog."""
    try:
        if not force:
            confirm = typer.confirm(
                f"Are you sure you want to delete model {name}:{version}?"
            )
            if not confirm:
                raise typer.Abort()
        
        catalog = ModelCatalog(config.storage.catalog_path)
        catalog.delete_model(name, version)
        
        console.print(f"[bold green]Model {name}:{version} deleted successfully[/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        raise typer.Exit(1)

@app.command()
def cleanup(
    max_backups: int = typer.Option(
        config.storage.max_backup_files,
        help="Maximum number of backup files to keep"
    )
):
    """Clean up old backup files."""
    try:
        catalog = ModelCatalog(config.storage.catalog_path)
        catalog.storage.cleanup_old_backups(max_backups)
        
        console.print("[bold green]Cleanup completed successfully[/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app() 