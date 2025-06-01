source .env
# prepare ollama gguf qwen3:0.6b
docker run -d --name ollama-tmpdown \
  -e HF_ENDPOINT=https://hf-mirror.com \
  -v ${DHOST_OLLAMA_DIR}:/root/.ollama \
    ollama/ollama
docker exec -it --name ollama-tmpdown \
    ollama pull qwen3:0.6b
docker rm -f ollama-tmpdown

# prepare vllm embedding BAAI/bge-m3
docker run -it --rm --entrypoint="" \
  -e HF_ENDPOINT=https://hf-mirror.com \
  -v ${DHOST_VLLM_HF_DIR}:/root/.cache/huggingface \
  -v ${DHOST_VLLM_MS_DIR}:/root/.cache/modelscope \
    vllm/vllm-openai \
      bash -c "modelscope download BAAI/bge-m3"

# prepare vllm reranker BAAI/bge-reranker-v2-m3
docker run -it --rm --entrypoint="" \
  -e HF_ENDPOINT=https://hf-mirror.com \
  -v ${DHOST_VLLM_HF_DIR}:/root/.cache/huggingface \
  -v ${DHOST_VLLM_MS_DIR}:/root/.cache/modelscope \
    vllm/vllm-openai \
      bash -c "modelscope download BAAI/bge-reranker-v2-m3"

# # prepare vllm Qwen/Qwen3-32B-AWQ
# docker run -it --rm --entrypoint="" \
#   -e HF_ENDPOINT=https://hf-mirror.com \
#   -v ${DHOST_VLLM_DIR}:/root/.cache/huggingface
#     vllm/vllm-openai \
#       bash -c "huggingface-cli download Qwen/Qwen3-32B-AWQ"
docker run -it --rm --entrypoint="" \
  -v ${DHOST_VLLM_HF_DIR}:/root/.cache/huggingface \
  -v ${DHOST_VLLM_MS_DIR}:/root/.cache/modelscope \
    vllm/vllm-openai \
      bash -c "modelscope download Qwen/Qwen3-32B-AWQ"

# prepare vllm Qwen/Qwen3-30B-A3B-GPTQ-Int4
docker run -it --rm --entrypoint="" \
  -v ${DHOST_VLLM_HF_DIR}:/root/.cache/huggingface \
  -v ${DHOST_VLLM_MS_DIR}:/root/.cache/modelscope \
    vllm/vllm-openai \
      bash -c "modelscope download Qwen/Qwen3-30B-A3B-GPTQ-Int4"

# prepare vllm Intel/DeepSeek-R1-0528-Qwen3-8B-int4-AutoRound-inc
docker run -it --rm --entrypoint="" \
  -e HF_ENDPOINT=https://hf-mirror.com \
  -v ${DHOST_VLLM_DIR}:/root/.cache/huggingface
    vllm/vllm-openai \
      bash -c "huggingface-cli download Intel/DeepSeek-R1-0528-Qwen3-8B-int4-AutoRound-inc"


# busybox fetch
docker create --name bb-tmp tmp busybox:uclibc
docker cp bb-tmp:/bin/busybox ./external/busybox
docker rm bb-tmp
chmod +x ./external/busybox

# create network
docker network create localai02 --subnet ${VIRBR_IPV4} --subnet ${VIRBR_IPV6}
