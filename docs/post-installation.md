# 📋 Post-Installation Setup Guide

After successfully deploying the Local AI Suite with `docker compose up -d`, follow these essential configuration steps to complete your setup.

## 🎯 Overview

This guide covers the critical "out-of-the-box" configurations needed for:

1. **OpenWebUI Configuration** - Admin panel settings, model visibility, interface settings
2. **OpenWebUI-Monitor Setup** - Usage tracking, billing, and monitoring integration
3. **System Verification** - Ensuring all components work together correctly

---

## 🔧 Part 1: OpenWebUI Configuration

### Step 1: Initial Admin Setup

1. **Access OpenWebUI Interface**
   ```bash
   # Open your browser and navigate to:
   http://<your-server-ip>:8080
   ```

2. **Create Admin Account**
   - Register the first user account (this becomes the admin)
   - Use a strong password and remember the credentials

### Step 2: Admin Panel Settings

Access the admin panel by clicking on your profile → **Admin Panel**.

#### 2.1 Model Configuration

**Models Visibility Settings:**
- Navigate to **Settings** → **Models**
- **Make the following models PUBLIC** (essential for proper functioning):
  
  | Model Type | Model Name | Visibility | Purpose |
  |------------|------------|------------|---------|
  | **Main LLM** | `Intel/DeepSeek-R1-0528-Qwen3-8B-int4-AutoRound-inc` | ✅ Public | Primary chat model |
  | **Task Model** | `qwen3:0.6b` | ✅ Public | Tool/function calling |
  | **Embedding** | `BAAI/bge-m3` | Internal | RAG embeddings |
  | **Reranker** | `BAAI/bge-reranker-v2-m3` | Internal | Search ranking |

> **⚠️ Important**: Task model (`qwen3:0.6b`) **MUST** be set to public for tool functions to work properly.

#### 2.2 Interface Settings

**External/Internal Model Configuration:**
- Go to **Settings** → **Interface**
- Configure the following for **Title Generation** and other automated tasks:

```yaml
Title Generation:
  Model: qwen3:0.6b
  Provider: Ollama

Query Generation:
  Model: qwen3:0.6b
  Provider: Ollama

Search Query Generation:
  Model: qwen3:0.6b
  Provider: Ollama
```

#### 2.3 Evaluation Settings

**Disable Arena Mode:**
- Navigate to **Settings** → **General** → **Evaluation**
- **Disable Arena Mode** (turn off the toggle)

> Arena mode can interfere with monitoring and cause unexpected behavior.

#### 2.4 Documents & RAG Settings

**Enable Reranking:**
- Go to **Settings** → **Documents**
- **Enable Reranking**: ✅ On
- **Reranking Model**: `BAAI/bge-reranker-v2-m3`
- **Top K**: `12` (adjust based on needs)
- **Top N**: `6` (adjust based on needs)

**Upload Limits:**
- Set **Max Upload Size**: `50MB` (or suitable value for your use case)
- **Allowed File Types**: Enable documents you need (PDF, DOCX, TXT, etc.)

#### 2.5 Network & API Settings

**RAG Configuration:**
- **Vector Database**: `pgvector` ✅
- **Embedding Model**: `BAAI/bge-m3`
- **Reranking Model**: `BAAI/bge-reranker-v2-m3`
- **Web Search**: `SearXNG` ✅
- **Content Extraction**: `Apache Tika` ✅

---

## 📊 Part 2: OpenWebUI-Monitor Setup

### Step 1: Get OpenWebUI API Key

1. **Access Your Profile Settings**
   - In OpenWebUI, click your profile picture
   - Go to **Account** → **API Keys**

2. **Generate API Key**
   - Click **Create new secret key**
   - Copy the generated API key (starts with `sk-...`)
   - **Save this key safely** - you'll need it for the monitor setup

### Step 2: Configure Environment Variables

1. **Update .env file**
   ```bash
   nano .env
   ```

2. **Set the following variables:**
   ```bash
   # OpenWebUI Monitor Configuration
   OPENWEBUI_DOMAIN=http://<your-server-ip>:8080
   OPENWEBUI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxx  # The API key from Step 1
   
   # Generate secure tokens 
   ACCESS_TOKEN=$(openssl rand -base64 32 | tr '+/' '-_' | tr -d '=')
   API_KEY=$(openssl rand -base64 32 | tr '+/' '-_' | tr -d '=')
   ```

3. **Restart the monitor service**
   ```bash
   docker compose restart openwebui-monitor
   ```

### Step 3: Add Monitor Functions to OpenWebUI

#### 3.1 Add Usage Monitor Function

1. **Access Functions Panel**
   - In OpenWebUI, go to **Workspace** → **Functions**
   - Click **+ Create Function**

2. **Import the Monitor Function**
   - Copy the content from `third_party/openwebui-monitor/openwebui_monitor.py`
   - Paste it in the function editor
   - Click **Save**

3. **Configure Function Valves**
   - Click on the function you just created
   - Go to **Valves** settings
   - Configure the following:

   ```yaml
   api_endpoint: http://<your-server-ip>:7878  # OpenWebUI-Monitor IP:Port
   # as it is frontend-app then we cannot directly access it
   # api_endpoint http://172.25.114.35:3000 
   api_key: YOUR_API_KEY  # The API_KEY from your .env file
   priority: 5
   language: zh  # or 'en' for English
   show_time_spent: true
   show_tokens_per_sec: true
   show_cost: true
   show_balance: true
   show_tokens: true
   ```

#### 3.2 Add Usage Button Function

1. **Create Another Function**
   - Click **+ Create Function** again
   - Copy content from `third_party/openwebui-monitor/get_usage_button.py`
   - Paste and save

2. **Configure Button Function**
   - Set the valves according to your display preferences:
   ```yaml
   show_cost: true
   show_balance: true
   show_tokens: true
   show_tokens_per_sec: true
   ```

> **Note**: Skip the `openwebui_monitor_invisible.py` file.

### Step 4: Verify Monitor Integration

1. **Check Monitor Dashboard**
   ```bash
   # Access the monitoring dashboard
   # Use ACCESS_TOKEN= set in Step 2 to login
   http://<your-server-ip>:7878
   ```

2. **Test Integration**
   - Send a test message in OpenWebUI
   - Verify usage statistics appear in the chat
   - Check that data appears in the monitor dashboard

---

## ✅ Part 3: System Verification

### Step 1: Service Health Check

```bash
# Check all services are running
docker compose ps

# Verify specific service logs
docker compose logs openwebui -f
docker compose logs openwebui-monitor -f
docker compose logs vllm -f
```

### Step 2: API Endpoints Verification

```bash
# Test main LLM
curl -X GET "http://<your-ip>:4997/v1/models" \
  -H "Authorization: Bearer sk-CUSTOMED-TOK"

# Test embedding service
curl -X GET "http://<your-ip>:4997/v1/models" \
  -H "Authorization: Bearer sk-CUSTOMED-TOK"

# Test OpenWebUI API
curl -X GET "http://<your-ip>:8080/api/v1/models" \
  -H "Authorization: Bearer owui-your-api-key"
```

### Step 3: RAG Pipeline Test

1. **Upload a test document** in OpenWebUI
2. **Ask questions** about the document content
3. **Verify** that:
   - Document is processed successfully
   - Embeddings are generated
   - Search results are reranked
   - Responses reference the document

### Step 4: Monitor Data Verification

1. **Generate some usage**:
   - Send multiple messages of varying lengths
   - Use different models if available
   - Upload and query documents

2. **Check monitoring data**:
   - Visit monitor dashboard at `http://<your-ip>:7878`
   - Verify user statistics are tracked
   - Check cost calculations are accurate
   - Confirm balance updates work

---

## 🔍 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Models not visible** | Ensure models are set to Public in Admin Panel |
| **Monitor not tracking usage** | Check API keys and function valve configuration |
| **RAG not working** | Verify database connections and model endpoints |
| **Functions not loading** | Check Docker network connectivity between services |

### Debug Commands

```bash
# Check network connectivity
docker exec -it localai-openwebui ping localai-vllm
docker exec -it localai-openwebui ping localai-openwebuimonit

# Check function logs
docker compose logs openwebui | grep -i function
docker compose logs openwebui | grep -i error

# Verify database connections
docker exec -it localai-pgsql pg_isready
docker exec -it localai-pgvector pg_isready
```

### Log Locations

```bash
# OpenWebUI logs
docker compose logs openwebui

# Monitor logs
docker compose logs openwebui-monitor

# Database logs
docker compose logs pgsql
docker compose logs pgvector
```

---

## 🎉 Completion Checklist

- [ ] ✅ Admin account created and configured
- [ ] ✅ Models set to appropriate visibility (Main + Task models public)
- [ ] ✅ Interface settings configured for internal models
- [ ] ✅ Arena mode disabled
- [ ] ✅ RAG and reranking configured
- [ ] ✅ Upload limits set appropriately
- [ ] ✅ OpenWebUI API key generated
- [ ] ✅ Monitor environment variables configured
- [ ] ✅ Monitor functions added and configured
- [ ] ✅ System verification completed
- [ ] ✅ All services healthy and responding

---

## 📞 Next Steps

After completing this setup:

1. **Check the [Performance Guide](performance-guide.md)** for optimization tips

**🎊 Congratulations! Your Local AI Suite is now fully configured and ready for production use.** 