# Open-WebUI within vLLM backend and other useful stuffs

**DON'T BE LOST IN THE DEPLOY GAME**

## prerequisite

Hardware 
* CPU >= 8c, single-thread score >=300 (cpu-z benchmark 17.01.64)
* Memory >= 128 GB
* GPU-enabled, Total Video Memory >= 24 GB, CUDA-arch `sm>=80`
* Storage >= 500 GB

In this demo , we using following configuration
* 24GB video memory GPU x 1
* vllm `BAAI/bge-m3` for embedding
* ~~vllm `swift/Qwen3-30B-A3B-AWQ` or `Qwen/Qwen3-32B-AWQ` for generation~~ [Updated 01/06] use `Intel/DeepSeek-R1-0528-Qwen3-8B-int4-AutoRound-inc` instead
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
# please read script first!
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
docker compose logs vllmemb -f
# rerank LLM
docker compose logs vllmrrk -f
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
|82.5, ~=19.44GB|main LLM |Qwen3-8B(AWQ/GPTQ/AutoRound-int4)| token generating |
|~= 1.8GB | embed LLM |BAAI/bge-m3 | RAG-specified vLLM |
|~= 1.8GB | reranker LLM |BAAI/bge-reranker-v2-m3 | RAG-specified vLLM |
|~= 0.5GB | reserved | - | reserved for multi-task |

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

```text
Qwen3-8B(AWQ/GPTQ/AutoRound-int4)
  num_kv_heads=4,head_dim=128,layer=48,fp8=1
  per token size = 8*128*36*1=36KB
  model token length = 32768 (train-set)
  model size = [params] 8.19 * ( [int4] 0.5 + [AWQ] **12**/ 64 )  = 5.63 GB
  active kv size per model-len = [k+v] 2 * 36KB * 32768 = 2.25 GB
  
throughput prompt   speed = [FP16   from `rtx3090`] 35.6 TFLOPS / 8.19B / [fp16->fp8] sqrt(2)  ~= 3074 tok/s
throughput generate speed = [mem-bw from `rtx3090`] 936.2 GT/s / 8.19B * [AWQ/GPTQ-int4] 2 ~= 228 tok/s
max kv-cache token size = (19.44GB - [model and kv occupied size] 5.63 GB - [pytorch-reserve] 0.6 GB) / [kv-size per-model-len ] 2.25GB * [model-len] 32768 ~= 192366 tok (5.87 x)
```

### Detailed deployment

#### [containerized] vLLM deployment
 https://github.com/vllm-project/vllm

just using vLLM official auto published container

```text
vllm/vllm-openai  v0.9.0.1
vllm/vllm-openai  v0.8.5.post1
```

container `vllm/vllm-openai:v0.9.0.1` built within `cuda-12.8`, `pytorch=2.7.0`
* vllm == 0.9.0.1
* flashinfer-python == 0.2.5
* transformers == 4.52.4
* pytorch == 2.7.0+cu128

container `vllm/vllm-openai:v0.8.5.post1` built within`cuda-12.4`, `pytorch=2.6`
* vllm == 0.8.5.post1
* flashinfer-python == 0.2.1.post2+cu124torch2.6
* transformers == 4.51.3
* pytorch == 2.6.0+cu124

```bash
# suppose we using docker-ce and has nvidia-container-toolkit loaded
docker pull vllm/vllm-openai
```
for mainland china model fetch purpose, refer following repository for using faster mirror registry
* [Mainland China Dockerhub mirror/registry](https://github.com/dongyubin/DockerHub)


#### [local] vLLM deployment

you can also directly install pre-compiled `vLLM` and other dependent stuff, which is a bit more complicated

##### basic venv creation

the official vLLM container using `uv` for lightweight virtual environment management, but now I'd stick to `conda/mamba` derived from HPC/data-science workload.
* [uv - An extremely fast Python package and project manager, written in Rust](https://github.com/astral-sh/uv)

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

```yaml
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
for more information, please refer 
* [SUSTech Open Source Mirrors](https://mirrors.sustech.edu.cn/help/) https://mirrors.sustech.edu.cn
* [NJU Mirrors](https://mirrors.nju.edu.cn/help/) https://mirrors.nju.edu.cn
* [Tsinghua Open Source Mirror](https://mirrors.tuna.tsinghua.edu.cn/help/anaconda/) https://mirrors.tuna.tsinghua.edu.cn
* [GeekPie Open Source Mirror](https://mirrors.shanghaitech.edu.cn/help/anaconda/) https://mirrors.shanghaitech.edu.cn


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

##### version matrix
**tl;dr** the following version matrix is like

|  cuda-ver | pytorch-ver | vllm-ver | flashinfer-ver| transformer |
|----------|-----------|-------------|---------------|-------------|
| cu118 | 2.6.0+cu118 | 0.8.5.post1+cu118 | 0.2.2+cu118torch2.6 | 4.51.3 (from vllm-dep) |
| cu124 | 2.6.0+cu124 | 0.8.5.post1+cu124 | 0.2.2+cu124torch2.6 | 4.51.3 (from vllm-dep) |
| cu128 | 2.7.0+cu128 | 0.9.0.1 (+cu128) | 0.2.5 (+cu128) | 4.53.1 (from vllm-dep) |


##### pre-compiled vLLM installation
[vllm-project/vllm](https://github.com/vllm-project/vllm/releases)
[vLLM Documents](https://docs.vllm.ai/en/latest/getting_started/installation/gpu.html?device=cuda)
currently official vLLM version is 0.9.0.1, PyPI published version is compiled within `cuda-12.8`

for those within older system-wide `nvidia-driver` cuda-version  supported, please using the following version given at the official release page
* `vllm-0.8.5.post1+cu118-cp38-abi3-manylinux1_x86_64` for `cu118` and `pytorch==2.6.0`
* `vllm-0.9.0.1+cu126-cp38-abi3-manylinux1_x86_64` for `cu126` and `pytorch==2.7.0`
* `pip install vllm` for `cu128` and `pytorch==2.7.0`

assume we've got `cu124` env, then running

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

for `vllm<=0.8.5`, vllm only support `flashinfer<=0.2.2`
for `vllm=0.9.0`, vllm support `flashinfer==0.2.5`

running following command to inst 

```bash
# add flashinfer support
# curl -LO https://github.com/flashinfer-ai/flashinfer/releases/download/v0.2.2.post1/flashinfer_python-0.2.2.post1+cu124torch2.6-cp38-abi3-linux_x86_64.whl
pip install ./flashinfer_python-0.2.2.post1+cu124torch2.6-cp38-abi3-linux_x86_64.whl
```

##### running vLLM as local openai-compatible API server

running the following command to start such a server

```bash
vllm serve Intel/DeepSeek-R1-0528-Qwen3-8B-int4-AutoRound-inc \
  --served-model-name Intel/DeepSeek-R1-0528-Qwen3-8B-int4-AutoRound-inc \
  --host 0.0.0.0 --port 4997 \
  --dtype=auto --tensor-parallel-size 1 --max-model-len 32768 --load-format auto \
  --quantization auto-round \
  --enable-chunked-prefill \
  --gpu-memory-utilization 0.825 --max-num-batched-tokens 512 --max-num-seqs 16 \
  --rope-scaling {"factor": 4.0, "original_max_position_embeddings": 32768, "rope_type": "yarn" } \
  --kv-cache-dtype fp8_e4m3 --calculate-kv-scales \
  --preemption-mode swap --enable-prefix-caching \
  --enable-reasoning --reasoning-parser deepseek_r1
```

the given parameter means is given below, you can type 
```bash
vllm serve --help | less
```

for more detailed explanation
* [vLLM Documents - Engine Arguments](https://docs.vllm.ai/en/latest/configuration/engine_args.html)

|parameter|mean|value|value2|
|---------|----|-----|------|
| **model select** | | | |
| / (--model) | which model to use| Intel/DeepSeek-R1-0528-Qwen3-8B-int4-AutoRound-inc | model url from `huggingface`/`modelscope` or local path|
|--served-model-name| api-respond model name | Intel/DeepSeek-R1-0528-Qwen3-8B-int4-AutoRound-inc |  any vaild string |
| **server ip** | | | |
|--host | vllm api-service bind address |0.0.0.0 | any local/external IP |
|--port | vllm api-svc listening port | 4997 | any unused port |
| **model load**| | | |
| --load-format auto | model weight load format | auto |  `safetensors` and so on |
|--dtype | model weight / activation datatype | auto | `half` `float16` `bfloat16` `float32` |
| --quantization | model quantization method | autoround | `autoround` `gptq` `awq` `gguf` |
|--max-model-len | model max token length | 32768| any `valid` number within usage limited by k-v cache|
| --rope-scaling | for extended token length | {"factor": 4.0, "original_max_position_embeddings": 32768, "rope_type": "yarn" } | any valid config accepted by model |
| **activation / kv-cache** | | | |
|--kv-cache-dtype | quantized kv-cache datatype |fp8_e4m3  | `fp8`(>=sm90) |
|--calculate-kv-scales | | - | |
| **parallel** | | | |
| --tensor-parallel-size | tensor paralleling | 1 | `num` for how many GPU/TPU/xPU to use |
| **usage**| | | |
| --gpu-memory-utilization | how much pct% of GPU memory to utilize | 0.825 | |
|--enable-chunked-prefill | make precompiled graph for better performance | | |
| --max-num-batched-tokens | max token contains in per batch |  512 | |
| --max-num-seqs | max concurrent compute request | 16  | |
| --enable-prefix-caching  | using cache for saving re-compute | | |
| --preemption-mode | when multiple request comes and kv-limited, how to cope | `swap` | `swap` for using a little system-memory in case of memory k-v limited, `recompute` for re compute if not enough, `None` for disable preempt feature|
| **CoT thinking** | | | |
| --enable-reasoning --reasoning-parser deepseek_r1 | force enabled model thinking| | |

#### [local] OpenWebUI
using containerized deployment 
please refering `docker-compose.yaml` for detailed info