"""Example script demonstrating model catalog usage."""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()

# Configuration
API_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin"

async def get_token() -> str:
    """Get authentication token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/token",
            data={"username": USERNAME, "password": PASSWORD}
        )
        return response.json()["access_token"]

def create_example_model():
    """Create example model entry."""
    return {
        "metadata": {
            "name": "bert-base-uncased",
            "version": "1.0.0",
            "framework": "pytorch",
            "task": "nlp",
            "precision": "fp16",
            "description": "BERT base uncased model optimized for inference",
            "tags": ["transformer", "bert", "nlp", "text-classification"],
            "inputs": {
                "input_ids": {
                    "shape": [-1, 512],
                    "dtype": "int64",
                    "description": "Token IDs"
                },
                "attention_mask": {
                    "shape": [-1, 512],
                    "dtype": "int64",
                    "description": "Attention mask"
                }
            },
            "outputs": {
                "logits": {
                    "shape": [-1, 2],
                    "dtype": "float32",
                    "description": "Classification logits"
                }
            },
            "performance_metrics": {
                "latency_ms": 15.5,
                "throughput": 128.0,
                "memory_mb": 420
            },
            "author": "SolidRusT Networks",
            "license": "MIT",
            "homepage": "https://huggingface.co/bert-base-uncased",
            "paper": "https://arxiv.org/abs/1810.04805",
            "min_gpu_memory": 4096,
            "recommended_batch_size": 32,
            "triton_platform": "pytorch",
            "triton_max_batch_size": 128
        },
        "documentation": {
            "overview": "BERT (Bidirectional Encoder Representations from Transformers) base uncased model...",
            "architecture": "The model consists of 12 transformer layers with 768 hidden dimensions...",
            "performance": "Optimized for inference with FP16 precision, achieving 15.5ms latency...",
            "limitations": "Maximum sequence length of 512 tokens, performance may degrade for longer sequences.",
            "examples": [
                {
                    "name": "Text Classification",
                    "description": "Example of binary text classification",
                    "code": """
import torch
from transformers import BertTokenizer, BertForSequenceClassification

tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model = BertForSequenceClassification.from_pretrained("bert-base-uncased")

text = "This movie is great!"
inputs = tokenizer(text, return_tensors="pt")
outputs = model(**inputs)
predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
""",
                    "inputs": {
                        "text": "This movie is great!"
                    },
                    "outputs": {
                        "positive_prob": 0.92,
                        "negative_prob": 0.08
                    }
                }
            ],
            "preprocessing": "Text is tokenized using the BERT tokenizer with maximum length of 512...",
            "postprocessing": "Apply softmax to logits to get class probabilities...",
            "references": [
                "https://arxiv.org/abs/1810.04805",
                "https://github.com/huggingface/transformers"
            ]
        }
    }

@app.command()
def add_model():
    """Add example model to catalog."""
    async def _add_model():
        token = await get_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/v2/catalog/models",
                headers=headers,
                json=create_example_model()
            )
            
            if response.status_code == 200:
                console.print("[green]Model added successfully!")
                console.print(json.dumps(response.json(), indent=2))
            else:
                console.print(f"[red]Error: {response.text}")
    
    asyncio.run(_add_model())

@app.command()
def list_models():
    """List models in catalog."""
    async def _list_models():
        token = await get_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/v2/catalog/models",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Create table
                table = Table(title="Model Catalog")
                table.add_column("Name")
                table.add_column("Version")
                table.add_column("Framework")
                table.add_column("Task")
                table.add_column("Precision")
                table.add_column("Tags")
                
                for model in data["models"]:
                    metadata = model["metadata"]
                    table.add_row(
                        metadata["name"],
                        metadata["version"],
                        metadata["framework"],
                        metadata["task"],
                        metadata["precision"],
                        ", ".join(metadata["tags"])
                    )
                
                console.print(table)
                
                # Print statistics
                console.print("\n[bold]Statistics:[/bold]")
                console.print(f"Total models: {data['total']}")
                console.print("\n[bold]Frameworks:[/bold]")
                for fw, count in data["frameworks"].items():
                    console.print(f"  {fw}: {count}")
                console.print("\n[bold]Tasks:[/bold]")
                for task, count in data["tasks"].items():
                    console.print(f"  {task}: {count}")
                console.print("\n[bold]Precisions:[/bold]")
                for prec, count in data["precisions"].items():
                    console.print(f"  {prec}: {count}")
            else:
                console.print(f"[red]Error: {response.text}")
    
    asyncio.run(_list_models())

@app.command()
def get_model(name: str, version: str):
    """Get model details."""
    async def _get_model():
        token = await get_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/v2/catalog/models/{name}/{version}",
                headers=headers
            )
            
            if response.status_code == 200:
                console.print(json.dumps(response.json(), indent=2))
            else:
                console.print(f"[red]Error: {response.text}")
    
    asyncio.run(_get_model())

@app.command()
def list_tags():
    """List all tags."""
    async def _list_tags():
        token = await get_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/v2/catalog/tags",
                headers=headers
            )
            
            if response.status_code == 200:
                tags = response.json()
                
                # Create table
                table = Table(title="Model Tags")
                table.add_column("Tag")
                table.add_column("Count")
                
                for tag, count in sorted(tags.items()):
                    table.add_row(tag, str(count))
                
                console.print(table)
            else:
                console.print(f"[red]Error: {response.text}")
    
    asyncio.run(_list_tags())

if __name__ == "__main__":
    app() 