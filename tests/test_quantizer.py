"""Test cases for the quantizer module."""

import pytest
from pathlib import Path
import torch

from srt_model_quantizing.quantizer import ModelQuantizer, QuantizationConfig
from srt_model_quantizing.utils.helpers import (
    check_gpu_availability,
    validate_precision,
    validate_output_dir
)

@pytest.fixture
def config():
    """Create a test configuration."""
    return QuantizationConfig(
        model_name="bert-base-uncased",
        output_dir=Path("./test_output"),
        precision="fp16",
        max_batch_size=1,
        dynamic_shapes=True
    )

def test_validate_precision():
    """Test precision validation."""
    assert validate_precision("fp16") == "fp16"
    assert validate_precision("int8") == "int8"
    
    with pytest.raises(ValueError):
        validate_precision("invalid")

def test_validate_output_dir(tmp_path):
    """Test output directory validation."""
    test_dir = tmp_path / "test_output"
    validated_path = validate_output_dir(test_dir)
    assert validated_path.exists()
    assert validated_path.is_dir()

@pytest.mark.skipif(not check_gpu_availability(), reason="GPU not available")
def test_model_quantizer_initialization(config):
    """Test ModelQuantizer initialization."""
    quantizer = ModelQuantizer(config)
    assert quantizer.config == config
    assert quantizer.logger is not None

@pytest.mark.skipif(not check_gpu_availability(), reason="GPU not available")
def test_model_preparation(config):
    """Test model preparation."""
    quantizer = ModelQuantizer(config)
    quantizer.prepare_model()
    assert quantizer.model is not None
    assert quantizer.tokenizer is not None

def test_config_validation():
    """Test configuration validation."""
    # Valid configuration
    config = QuantizationConfig(
        model_name="bert-base-uncased",
        output_dir=Path("./test_output"),
        precision="fp16"
    )
    assert config.model_name == "bert-base-uncased"
    assert config.precision == "fp16"
    
    # Invalid precision
    with pytest.raises(ValueError):
        QuantizationConfig(
            model_name="bert-base-uncased",
            output_dir=Path("./test_output"),
            precision="invalid"
        ) 