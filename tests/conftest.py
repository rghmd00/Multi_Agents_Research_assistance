import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def pytest_configure(config):
    config.addinivalue_line("markers", "eval: slow LLM-as-judge tests, requires Ollama")
    config.addinivalue_line("markers", "unit: fast tests, no external deps")


@pytest.fixture
def sample_sources_content():
    """Known-good source material for faithfulness testing — mirrors
    closures_note_content, but for a research topic instead of a code concept."""
    notes_path = Path(__file__).parent.parent / "study_materials/sample_sources/transformers.md"
    if notes_path.exists():
        return notes_path.read_text(encoding="utf-8")
    return """
# Transformer Architecture (sample source)

The Transformer was introduced in "Attention Is All You Need" (2017).
It relies entirely on self-attention mechanisms, removing recurrence
and convolution. Key components: multi-head attention, positional
encodings, and feedforward layers. It enabled significant parallelization
during training compared to RNNs.
"""