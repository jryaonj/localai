# Containerized Deployment Guide

## Container Versions and Dependencies

### vLLM Backend
- `vllm/vllm-openai:v0.9.0.1`
  - CUDA 12.8
  - PyTorch 2.7.0
  - vLLM 0.9.0.1
  - FlashInfer 0.2.5
  - Transformers 4.52.4

- `vllm/vllm-openai:v0.8.5.post1`
  - CUDA 12.4
  - PyTorch 2.6.0
  - vLLM 0.8.5.post1
  - FlashInfer 0.2.1.post2
  - Transformers 4.51.3

### Other Components
- Open-WebUI: Latest version
- SearXNG: Latest version
- Apache Tika: Latest version
- Postgres/pgvector: 0.8.0-pg17

## Quick Setup

1. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

2. Pull required Docker images (optional for blocked access/slow network):
```bash
# For users with limited Docker Hub access or slow networks
# Edit DOCKERHUBPXY and GHCRPXY variables in init_dockerimg.sh if needed
bash init_dockerimg.sh
```

3. Download models:
```bash
bash init_modelfiles.sh
```

4. Launch services:
```bash
docker compose up -d
```

## Network Configuration

Uses Docker network `localai02` with:
- IPv4 subnet: 172.25.114.0/24 
- IPv6 subnet: fd80:dd00:a114::/48

## Container Health Checks

All services include health checks:
- vLLM services: Check model API endpoint
- Databases: Check connection
- Web services: Check HTTP endpoints

For mainland China users, configure mirrors in `.env`:
```bash
HF_ENDPOINT=https://hf-mirror.com
```