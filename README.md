# E-Commerce Agent Crew Locally

## Hardware Info

```
- Quadro RTX 5000 (16 GB VRAM)
- 32 GB RAM
```

## Compatible Model Table for the GPU

| Model | Size / Quantization | VRAM Usage | Status & Performance |
| :--- | :--- | :--- | :--- |
| **Qwen2.5-Coder 14B** | Q4_K_M or Q5_K_M | ~9.5 – 10.5 GB | **Most Ideal Option.** Fits entirely in VRAM, leaving room for a 16k context window. Delivers ~35-45 tokens/sec. |
| **DeepSeek-R1-Distill-Qwen-14B** | Q4_K_M | ~9.5 GB | **Reasoning:** Executes Chain-of-Thought for complex autonomous decisions. |
| **Qwen3 14B** | Q4_K_M | ~9.5 GB | Highly stable in general autonomous tasks, multilingual performance, and tool calling. |
| **Qwen2.5-Coder 32B** | Q3_K_M / Q4_K_M | ~13.5 GB + CPU RAM | The portion exceeding VRAM is offloaded to 32 GB RAM. Speed drops to ~8–12 tokens/sec, but intelligence increases significantly. |

## 1. Create and activate env

```bash
sudo apt install python3.11
```

```bash
sudo apt install python3.11-venv
```

```bash
python3.11 -m venv agent_env
```

```bash
source agent_env/bin/activate
```

## 2. Install Packages

```bash
pip install -r requirements.txt
```
