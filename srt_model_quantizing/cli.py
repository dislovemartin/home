"""Command-line interface for the SRT Model Quantizing tool."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from srt_model_quantizing.quantizer import ModelQuantizer, QuantizationConfig

app = typer.Typer(help="SRT Model Quantizing - A pipeline for model quantization using NVIDIA NIM")
console = Console()

@app.command()
def quantize(
    model_name: str = typer.Argument(..., help="Name or path of the model to quantize"),
    output_dir: Path = typer.Option(
        Path("./quantized_models"),
        "--output-dir", "-o",
        help="Directory to save the quantized model"
    ),
    precision: str = typer.Option(
        "fp16",
        "--precision", "-p",
        help="Quantization precision (fp16, int8)"
    ),
    max_batch_size: int = typer.Option(
        1,
        "--max-batch-size", "-b",
        help="Maximum batch size for inference"
    ),
    dynamic_shapes: bool = typer.Option(
        True,
        "--dynamic-shapes/--no-dynamic-shapes",
        help="Enable/disable dynamic shapes"
    ),
    calibration_data: Optional[str] = typer.Option(
        None,
        "--calibration-data", "-c",
        help="Path to calibration data for INT8 quantization"
    )
) -> None:
    """Quantize a model using NVIDIA NIM."""
    try:
        config = QuantizationConfig(
            model_name=model_name,
            output_dir=output_dir,
            precision=precision,
            max_batch_size=max_batch_size,
            dynamic_shapes=dynamic_shapes,
            calibration_data=calibration_data
        )
        
        quantizer = ModelQuantizer(config)
        quantizer.quantize()
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}")
        raise typer.Exit(1)

@app.command()
def version():
    """Display the version of SRT Model Quantizing."""
    from srt_model_quantizing import __version__
    console.print(f"SRT Model Quantizing v{__version__}")

if __name__ == "__main__":
    app() 