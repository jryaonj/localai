# Local AI Deployment with Open-WebUI and vLLM Backend

An end-to-end solution for deploying local AI services with optimized performance and resource utilization.

## Overview

This project provides a complete setup for running local AI services using:
- [vLLM](https://docs.vllm.ai/) as the high-performance inference backend
- [Open-WebUI](https://openwebui.com/) as the user interface
- [SearXNG](https://docs.searxng.org/) for web search capabilities 
- [Apache Tika](https://github.com/apache/tika) for document processing
- [PostgreSQL](https://www.postgresql.org/) for data persistence
- [OpenWebUI-Monitor](https://github.com/VariantConst/OpenWebUI-Monitor) for detailed user-activity tracking, quota management, and cost accounting

## Prerequisites

### Hardware Requirements
- CPU: ≥ 8 cores (single-thread score ≥300 on CPU-Z benchmark 17.01.64)
- RAM: ≥ 128 GB
- GPU: NVIDIA GPU with ≥24GB VRAM (CUDA architecture sm80 or higher)
- Storage: ≥ 500 GB

### Reference Configuration
Our tested setup uses:
- 1x NVIDIA RTX 3090 (24GB VRAM)
- Models:
  - Main LLM: Intel/DeepSeek-R1-0528-Qwen3-8B-int4-AutoRound-inc
  - Embedding: BAAI/bge-m3
  - Reranker: BAAI/bge-reranker-v2-m3
  - Auxiliary: ollama qwen3:0.6b

## Quick Start

1. Configure environment:
```bash
# Edit .env file with your settings
cp .env.example .env
```

2. Download required models:
```bash
bash init_modelfiles.sh
```

3. Launch services:
```bash
docker compose up -d
```

4. Monitor deployment:
```bash
# Check main LLM
docker compose logs vllm -f
# Check embedding model
docker compose logs vllmemb -f
# Check reranker
docker compose logs vllmrrk -f
# Check UI
docker compose logs openwebui -f
```

5. Access the interface:
```bash
xdg-open http://<your-ip>:8080
```

## Resource Planning

| Component | Memory | Model | Purpose |
|-----------|---------|-------|---------|
| Main LLM | 19.44GB | Qwen3-8B(int4) | Token generation |
| Embedding | 1.8GB | BAAI/bge-m3 | RAG embeddings |
| Reranker | 1.8GB | BAAI/bge-reranker-v2-m3 | RAG reranking |
| Reserved | 0.5GB | - | Multi-tasking buffer |

## Deployment Options

### Containerized (Recommended)
See [Containerized Deployment Guide](docs/containerized-deployment.md) for details about:
- Container versions and compatibility  
- Mirror registries for faster downloads
- Environment configuration

### Local Installation 
See [Local Installation Guide](docs/local-installation.md) for:
- Python environment setup
- vLLM installation steps
- Model deployment process

## Performance

Theoretical metrics for Qwen3-8B(int4):
- Prompt processing: ~3074 tokens/s
- Generation speed: ~228 tokens/s  
- Max context length: 192366 tokens

For detailed performance analysis and tuning, see [Performance Guide](docs/performance.md).

## License

MIT License

## Components & References

- [vLLM](https://docs.vllm.ai/)
- [Open WebUI](https://openwebui.com/)
- [SearXNG](https://docs.searxng.org/)
- [Apache Tika](https://github.com/apache/tika)
- [OpenWebUI-Monitor](https://github.com/VariantConst/OpenWebUI-Monitor)