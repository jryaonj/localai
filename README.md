# Open-WebUI within vLLM backend and other useful stuffs

**DON'T BE BOTTLENECK**

Stop fiddling servers—start shaping ideas.
If you find this manual useful, just freeze and move on

## prerequisite

Hardware 
* CPU >= 8c, single-thread score >=300 (cpu-z benchmark 17.01.64)
* Memory >= 128 GB
* GPU-enabled, Total Video Memory >= 24 GB, CUDA-arch `sm>=80`
* Storage >= 500 GB

In this demo , we using following configuration
* 24GB video memory GPU x 1
* vllm `BAAI/bge-m3` for embedding
* vllm `swift/Qwen3-30B-A3B-AWQ` or `Qwen/Qwen3-32B-AWQ` for generation
* ollama `qwen3:0.6b` for title generation and other task 

## components

* [vLLM](https://docs.vllm.ai/en/latest/index.html)
* [vllm-project/vllm](https://github.com/vllm-project/vllm/releases)
* [Open WebUI](https://openwebui.com/)
* [open-webui/open-webui](https://github.com/open-webui/open-webui)
* [Tika](https://github.com/apache/tika)
* [SearXNG](https://github.com/searxng/searxng)
* [SearXNG Documentation](https://docs.searxng.org/)

## deployment
### Docker Compose , quick

customized following parameters in `.env`


after customized `.env` file, run following command to download modelfile 

```bash
bash init_modelfiles.sh
```

then set up all service by docker compose

```bash
docker compose up -d
```

checking the progress of the model serve preparation
```bash
# main-LLM
docker compose logs vllm -f
# embed LLM
docker compose logs vllm-embed -f
# rerank LLM
docker compose logs vllm-embed -f
# open-webui
docker compose logs openwebui -f
```

after model seems standby, access your in browser and everything should be ok

```bash
# suppose ip:port of openwebui is 172.25.114:9:8080, then
xdg-open http://172.25.114.9:8080
```

for host-guset port-mapping, please refer `docker-compose.yaml`

### capacity estimation - special memory allocation plan

**example - 1x NVIDIA RTX 3090 GPU w. 24GB video memory**

allocation plan as is

|% of vMEM|Role|Model|Description|
|---------|-----|-----------|-----|
|82.5, ~=19.9GB|main LLM |Qwen3-30B-A3B(AWQ/GPTQ-int4)| token generating |
|~= 1.8GB | embed LLM |BAAI/bge-m3 | RAG-specified vLLM |
|~= 1.8GB | reranker LLM |BAAI/bge-reranker-v2-m3 | RAG-specified vLLM |
|~= 0.5GB | reserved | - | un-allocated |

estimate theoretical token speed of the main-LLM (30B, 3B active) is like

```text
Qwen3-30B-A3B(AWQ/GPTQ-int4)
  num_kv_heads=4,head_dim=128,layer=48,fp8=1
  per token size = 4*128*48*1=24KB
  model token length = 32768 (train-set)
  model size = [params] 30.53 * ( [int4] 0.5 + [AWQ] 3/ 64 )  = 16.70 GB
  active kv size per model-len = [k+v] 2 * 24KB * 32768 = 1.5 GB
  
throughput prompt   speed = [FP16   from `rtx3090`] 35.6 TFLOPS / 30.53B / [fp16->fp8] sqrt(2)  ~= 820 tok/s
throughput generate speed = [mem-bw from `rtx3090`] 936.2 GT/s / 3B * [AWQ/GPTQ-int4] 2 ~= 624 tok/s
max kv-cache token size = (19.9GB - [model and kv occupied size] 16.70 GB) / [kv-size per-model-len ] 1.5GB * [model-len] 32768 ~= 67806 tok (1.04 x)
```

### Detailed

#### [containerized] vLLM deployment
 https://github.com/vllm-project/vllm

just using vLLM official auto published container

container within built-in `cuda-12.4`, `pytorch=2.6`
* vllm == 0.8.5.post1
* flashinfer-python == 0.2.1.post2+cu124torch2.6
* transformers == 4.51.3

```bash
# suppose we using docker-ce and has nvidia-container-toolkit loaded
docker pull vllm/vllm-openai
```

for mainland china model fetch purpose, using following command to add 

#### [local] vLLM deployment

##### basic venv creation
###### mamba-conda installation
[conda-forge/miniforge](https://github.com/conda-forge/miniforge)

using `Miniforge3` for virtual python environment creation

```bash
# download and install base env
curl -LO "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
chmod +x Miniforge3-$(uname)-$(uname -m).sh
# for system-wide support
# choose a global folder, like /opt/miniforge3
bash Miniforge3-$(uname)-$(uname -m).sh
```

then setting conda environment by edit/add `.condarc` at `~` user homedir

```rc
channels:
  - conda-forge
auto_activate_base: false
show_channel_urls: true
# for root user the location is miniforge installation location /opt/miniforge3
# for other local user, the location should be customized
# envs_dirs:
#   - /root/miniforge3/envs
```


for user in mainland china, using following `.condarc` to set nearest mirror
```rc
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
# for root user the location is miniforge installation location /opt/miniforge3
# envs_dirs:
#   - /root/miniforge3/envs
```

and do not forget to set the `PyPI` mirrors

```bash
# load global miniforge base
eval "$(/opt//miniforge3/bin/mamba' 'shell.bash' 'hook' 2> /dev/null)"
pip config set global.index-url https://mirrors.sustech.edu.cn/pypi/web/simple
```

here we choose conda mirror site `mirrors.sustech.edu.cn` provided by `SUStech`, there are other mirrors like 

* https://mirrors.sustech.edu.cn
* https://mirrors.nju.edu.cn
* https://mirrors.tuna.tsinghua.edu.cn
* https://mirrors.shanghaitech.edu.cn


for more information, please refer 
[SUSTech Open Source Mirrors](https://mirrors.sustech.edu.cn/help/)
[NJU Mirrors](https://mirrors.nju.edu.cn/help/)
[Tsinghua Open Source Mirror](https://mirrors.tuna.tsinghua.edu.cn/help/anaconda/)
[GeekPie Open Source Mirror](https://mirrors.shanghaitech.edu.cn/help/anaconda/)


###### new virtual environment creation

create a new environment named `vllm-local`, within `python=3.12` for further vllm installation

```bash
# first load global miniforge base
eval "$(/opt//miniforge3/bin/mamba' 'shell.bash' 'hook' 2> /dev/null)"
# then create new enviromnent
mamba create -n vllm-local python=3.12
```

after creation, use following command to activate it and enter

```bash
mamba activate vllm-local
# exit current venv
# mamba deactivate
```


##### pre-compiled vLLM installation
[vllm-project/vllm](https://github.com/vllm-project/vllm/releases)
[vLLM Documents](https://docs.vllm.ai/en/latest/getting_started/installation/gpu.html?device=cuda)
currently official vLLM version is 0.8.5, PyPI published version is compiled within cuda-12.4

for those within older system-wide `nvidia-driver` cuda-version supported, please using the following version given at the official release page
* `vllm-0.8.5.post1+cu118-cp38-abi3-manylinux1_x86_64`

```bash
# vllm and pytorch
# current pre-compiled 0.8.5 within cuda124
PYTOUCH_WHL_MIRROR=https://download.pytorch.org/whl
CUDA_VER=124
pip install vllm --extra-index-url ${PYTOUCH_WHL_MIRROR}/cu${CUDA_VER}
```

for user in mainland china, using following mirror site
```bash
# vllm and pytorch
# current pre-compiled 0.8.5 within cuda124
PYTOUCH_WHL_MIRROR=https://mirrors.aliyun.com/pytorch-wheels
CUDA_VER=124
pip install vllm --extra-index-url ${PYTOUCH_WHL_MIRROR}/cu${CUDA_VER}
```

##### FlashInfer adding

[FlashInfer: Kernel Library for LLM Serving](https://github.com/flashinfer-ai/flashinfer)
[Quantization - vLLM](https://docs.vllm.ai/en/latest/features/quantization/fp8.html)

currently (2025.03), vllm only support flashinfer<=0.2.2

```bash
# add flashinfer support
# curl -LO https://github.com/flashinfer-ai/flashinfer/releases/download/v0.2.2.post1/flashinfer_python-0.2.2.post1+cu124torch2.6-cp38-abi3-linux_x86_64.whl
pip install ./flashinfer_python-0.2.2.post1+cu124torch2.6-cp38-abi3-linux_x86_64.whl
```

