# Local Installation Guide

## Python Environment Setup

### About Virtual Environments
The official vLLM container uses `uv` for lightweight virtual environment management, but we'll use `conda/mamba` which is common in HPC/data-science workloads.

For reference:
- [uv](https://github.com/astral-sh/uv) - A fast Python package manager written in Rust
- [conda-forge/miniforge](https://github.com/conda-forge/miniforge) - Our chosen environment manager

### Install Miniforge3
```bash
# Download and install base env
curl -LO "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
chmod +x Miniforge3-$(uname)-$(uname -m).sh
# For system-wide support, choose a global folder like /opt/miniforge3
bash Miniforge3-$(uname)-$(uname -m).sh
```

### Configure Conda
Create `.condarc` in home directory:

```yaml
channels:
  - conda-forge
auto_activate_base: false
show_channel_urls: true
# For root user: miniforge installation location /opt/miniforge3
# envs_dirs:
#   - /root/miniforge3/envs
```

For users in mainland China, use this alternative `.condarc`:

```yaml
channels:
  - conda-forge
auto_activate_base: false
show_channel_urls: true
default_channels:
  - https://mirrors.sustech.edu.cn/anaconda/pkgs/main
  - https://mirrors.sustech.edu.cn/anaconda/pkgs/free
  - https://mirrors.sustech.edu.cn/anaconda/pkgs/r
  - https://mirrors.sustech.edu.cn/anaconda/pkgs/pro
  - https://mirrors.sustech.edu.cn/anaconda/pkgs/msys2
custom_channels:
  conda-forge: https://mirrors.sustech.edu.cn/anaconda/cloud
  msys2: https://mirrors.sustech.edu.cn/anaconda/cloud
  bioconda: https://mirrors.sustech.edu.cn/anaconda/cloud
  menpo: https://mirrors.sustech.edu.cn/anaconda/cloud
  pytorch: https://mirrors.sustech.edu.cn/anaconda/cloud
  simpleitk: https://mirrors.sustech.edu.cn/anaconda/cloud
  nvidia: https://mirrors.sustech.edu.cn/anaconda-extra/cloud
```

### Configure PyPI Mirrors (Optional)
For faster package downloads:

```bash
# Load global miniforge base
eval "$(/opt/miniforge3/bin/mamba shell.bash hook 2> /dev/null)"
pip config set global.index-url https://mirrors.sustech.edu.cn/pypi/web/simple
```

Available mirror options:
- [SUSTech Mirrors](https://mirrors.sustech.edu.cn)
- [NJU Mirrors](https://mirrors.nju.edu.cn)
- [Tsinghua Mirrors](https://mirrors.tuna.tsinghua.edu.cn)
- [ShanghaiTech Mirrors](https://mirrors.shanghaitech.edu.cn)

### Create vLLM Environment
```bash
# Load miniforge
eval "$(/opt/miniforge3/bin/mamba shell.bash hook)"
# Create new environment
mamba create -n vllm-local python=3.12
# Activate environment
mamba activate vllm-local
```

## Install vLLM

### Version Matrix
|CUDA|PyTorch|vLLM|FlashInfer|Transformers|
|----|--------|-----|-----------|------------|
|11.8|2.6.0|0.8.5.post1|0.2.2|4.51.3|
|12.4|2.6.0|0.8.5.post1|0.2.2|4.51.3|
|12.8|2.7.0|0.9.0.1|0.2.5|4.53.1|

### Installation Steps
```bash
PYTORCH_MIRROR=https://download.pytorch.org/whl
CUDA_VER=124
pip install vllm --extra-index-url ${PYTORCH_MIRROR}/cu${CUDA_VER}
```

### Install FlashInfer
```bash
pip install flashinfer-python
```

## Running vLLM Server
```bash
vllm serve <model-name> \
  --host 0.0.0.0 \
  --port 4997 \
  --dtype auto \
  --quantization auto-round \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.825
```