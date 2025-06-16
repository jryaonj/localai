# Local AI Deployment with Open-WebUI and vLLM Backend

An end-to-end solution for deploying local AI services with optimized performance and resource utilization.

## Overview

This project provides a complete setup for running local AI services using:
- [vLLM](https://docs.vllm.ai/) as the high-performance inference backend (text-only)
- [vLLM-MM](https://docs.vllm.ai/en/latest/multimodal.html) for multi-modal (vision-language) inference
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
  - Main LLM: Qwen/Qwen3-4B-AWQ (text, thinking, etc)
  - Embedding: BAAI/bge-m3
  - Reranker: BAAI/bge-reranker-v2-m3
  - Multi-Modal LLM: Qwen/Qwen2.5-VL-3B-Instruct-AWQ (image understanding)
  - Auxiliary: ollama qwen3:0.6b
  - [Optional] Image Generation: ComfyUI (self-built, keep caution on VRAM usage!)

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
# Check docker-compose.yaml first
# and do extra step when enable comfyui feature
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
# Check multi-modal LLM
docker compose logs vllmmm -f
```

5. Access the interface:
```bash
xdg-open http://<your-ip>:8080
```

## Resource Planning

| Component | Memory | Model | Purpose |
|-----------|---------|-------|---------|
| Main LLM | 9.1GB | Qwen3-4B(int4) | Token generation |
| Embedding | 1.8GB | BAAI/bge-m3 | RAG embeddings |
| Reranker | 2.0GB | BAAI/bge-reranker-v2-m3 | RAG reranking |
| Multi-Modal LLM | 10.1GB | Qwen2.5-VL-3B(int4) | Vision-Language generation |
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

Theoretical metrics for Qwen3-4B(int4):
- Prompt processing:  ~6293 tokens/s
- Generation speed:   ~468 tokens/s  
- Max context length: 32768 tokens x2.41 (0.395 utilization on RTX 3090 24GB)

For detailed performance analysis and tuning, see [Performance Guide](docs/performance.md).

## License

MIT License

## Components & References

- [vLLM](https://docs.vllm.ai/)
- [Open WebUI](https://openwebui.com/)
- [SearXNG](https://docs.searxng.org/)
- [Apache Tika](https://github.com/apache/tika)
- [OpenWebUI-Monitor](https://github.com/VariantConst/OpenWebUI-Monitor)
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- [Qwen](https://qwenlm.github.io/)
- [Hugging Face](https://huggingface.co/)
- [ModelScope](https://www.modelscope.cn/)


