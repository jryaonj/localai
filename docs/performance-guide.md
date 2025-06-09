# Performance Guide

## Memory Allocation (RTX 3090 24GB)

|Component|Memory|Model|Purpose|
|---------|------|-----|-------|
|Main LLM|19.44GB|Qwen3-8B(int4)|Token generation|
|Embedding|1.8GB|BAAI/bge-m3|RAG embeddings|
|Reranker|1.8GB|BAAI/bge-reranker-v2-m3|RAG reranking|
|Reserved|0.5GB|-|Multi-tasking buffer|

## Performance Metrics

### Qwen3-8B(int4) Model
- Prompt processing: ~3074 tokens/s
- Generation speed: ~228 tokens/s
- Max context length: 192366 tokens
- Model parameters: 8.19B
- Model size: 5.63GB
- KV cache per length: 2.25GB

### Architectural Details
```text
Configuration:
- num_kv_heads: 4
- head_dim: 128
- layers: 48
- fp8: 1
- per token size: 36KB
- model token length: 32768 (train-set)
```

## Performance Calculation

### Token Processing
```text
Prompt speed = [35.6 TFLOPS] / [8.19B params] / sqrt(2) ≈ 3074 tok/s
Generate speed = [936.2 GT/s] / [8.19B] * 2 ≈ 228 tok/s
```

### Memory Usage
```text
Model size = 8.19B * (0.5 + 12/64) = 5.63GB
KV cache = 2 * 36KB * 32768 = 2.25GB
Max tokens = (19.44GB - 5.63GB - 0.6GB) / 2.25GB * 32768 ≈ 192366
```