"""AI service for chat completion - supports 7 models"""
import os
from dataclasses import dataclass
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import Literal, AsyncGenerator, Optional

load_dotenv()

# Supported models
ModelType = Literal[
    "glm-4.7",
    "glm-4.7-flash",
    "deepseek",
    "doubao",
    "qwen",
    "qwen-flash",
    "hunyuan",
    "kimi",
    "minimax"
]

# Model configurations
MODEL_CONFIGS = {
    "glm-4.7": {
        "key": os.getenv("GLM_4_7_KEY"),
        "base_url": os.getenv("GLM_4_7_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
        "model": os.getenv("GLM_4_7_MODEL", "glm-4.7")
    },
    "glm-4.7-flash": {
        "key": os.getenv("GLM_4_7_FLASH_KEY"),
        "base_url": os.getenv("GLM_4_7_FLASH_BASE_URL", os.getenv("GLM_4_7_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")),
        "model": os.getenv("GLM_4_7_FLASH_MODEL", "glm-4.7-flash")
    },
    "deepseek": {
        "key": os.getenv("DEEPSEEK_KEY"),
        "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    },
    "doubao": {
        "key": os.getenv("DOUBAO_KEY"),
        "base_url": os.getenv("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
        "model": os.getenv("DOUBAO_MODEL", "ep-20241225172630-hkqxt")
    },
    "qwen": {
        "key": os.getenv("QWEN_KEY"),
        "base_url": os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        "model": os.getenv("QWEN_MODEL", "qwen-max-latest")
    },
    "qwen-flash": {
        "key": os.getenv("QWEN_FLASH_KEY"),
        "base_url": os.getenv("QWEN_FLASH_BASE_URL", os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")),
        "model": os.getenv("QWEN_FLASH_MODEL", "qwen-flash")
    },
    "hunyuan": {
        "key": os.getenv("HUNYUAN_KEY"),
        "base_url": os.getenv("HUNYUAN_BASE_URL", "https://api.hunyuan.cloud/v1"),
        "model": os.getenv("HUNYUAN_MODEL", "hunyuan-2.0-thinking-20251109")
    },
    "kimi": {
        "key": os.getenv("KIMI_KEY"),
        "base_url": os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1"),
        "model": os.getenv("KIMI_MODEL", "kimi-k2-thinking")
    },
    "minimax": {
        "key": os.getenv("MINIMAX_KEY"),
        "base_url": os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1"),
        "model": os.getenv("MINIMAX_MODEL", "abab6.5s-mini")
    }
}

# Default model
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "glm-4.7")

# Zaoya system prompt
SYSTEM_PROMPT = """You are Zaoya, an AI assistant that generates mobile-first web pages.

Rules:
1. Generate HTML with Tailwind CSS classes
2. Use semantic HTML5 elements
3. Mobile-first design (max-width: 428px viewport recommended)
4. Only use Zaoya.* JavaScript helpers for interactivity
5. Do not include external scripts or stylesheets (no CDN links). Do not include <script> tags; Zaoya injects runtime and Tailwind CSS.
6. Return response in this format:

```html
<!-- Your HTML here -->
```

```javascript
// Optional: DOM event wiring using Zaoya.* only
```

Available Zaoya.* helpers:
- Zaoya.submitForm(formData)
- Zaoya.track(event, data)
- Zaoya.toast(message)
- Zaoya.navigate(path)

Design guidelines:
- Use emoji icons instead of images
- Make touch-friendly buttons (min 44px height)
- Use safe area insets for mobile
- Smooth transitions and animations
- Clean, modern aesthetic
"""


def get_client(model_key: str = "glm-4.7") -> AsyncOpenAI:
    """Get OpenAI client for specified model"""
    config = MODEL_CONFIGS.get(model_key, MODEL_CONFIGS["glm-4.7"])
    return AsyncOpenAI(
        api_key=config["key"],
        base_url=config["base_url"]
    )


def get_model_name(model_key: str = "glm-4.7") -> str:
    """Get actual model name for API calls"""
    config = MODEL_CONFIGS.get(model_key, MODEL_CONFIGS["glm-4.7"])
    return config["model"]


@dataclass
class LLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    content: str
    usage: LLMUsage
    model: str


async def chat_complete(
    *,
    model: str = DEFAULT_MODEL,
    messages: list,
    temperature: float = 0.3,
) -> LLMResponse:
    """Generate a non-streaming response with fully specified messages."""
    client = get_client(model)
    model_name = get_model_name(model)

    response = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        stream=False,
    )

    usage_payload = response.usage or None
    usage = LLMUsage(
        prompt_tokens=getattr(usage_payload, "prompt_tokens", 0) or 0,
        completion_tokens=getattr(usage_payload, "completion_tokens", 0) or 0,
        total_tokens=getattr(usage_payload, "total_tokens", 0) or 0,
    )

    if response.choices and response.choices[0].message:
        return LLMResponse(
            content=response.choices[0].message.content or "",
            usage=usage,
            model=model_name,
        )

    return LLMResponse(content="", usage=usage, model=model_name)


async def stream_chat(
    messages: list,
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
) -> AsyncGenerator:
    """Stream chat completion from AI

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model identifier (glm-4.7, deepseek, etc.)
    """
    client = get_client(model)
    model_name = get_model_name(model)

    # Format messages with system prompt
    messages_formatted = [
        {"role": "system", "content": system_prompt or SYSTEM_PROMPT}
    ]

    for msg in messages:
        messages_formatted.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    stream = await client.chat.completions.create(
        model=model_name,
        messages=messages_formatted,
        stream=True
    )

    return stream


async def generate_response(
    messages: list,
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
) -> str:
    """Generate a non-streaming response from AI."""
    client = get_client(model)
    model_name = get_model_name(model)

    messages_formatted = [
        {"role": "system", "content": system_prompt or SYSTEM_PROMPT}
    ]
    for msg in messages:
        messages_formatted.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    request_payload = {
        "model": model_name,
        "messages": messages_formatted,
        "stream": False,
    }
    if temperature is not None:
        request_payload["temperature"] = temperature

    response = await client.chat.completions.create(**request_payload)

    if response.choices and response.choices[0].message:
        return response.choices[0].message.content or ""

    return ""


def get_available_models() -> list[dict]:
    """Get list of available AI models"""
    return [
        {"id": "glm-4.7", "name": "GLM-4.7", "provider": "智谱 AI"},
        {"id": "glm-4.7-flash", "name": "GLM-4.7 Flash", "provider": "智谱 AI"},
        {"id": "deepseek", "name": "DeepSeek V3", "provider": "DeepSeek"},
        {"id": "doubao", "name": "豆包 Doubao", "provider": "字节跳动"},
        {"id": "qwen", "name": "通义千问 Qwen Max", "provider": "阿里云"},
        {"id": "qwen-flash", "name": "通义千问 Qwen Flash", "provider": "阿里云"},
        {"id": "hunyuan", "name": "混元 Hunyuan", "provider": "腾讯"},
        {"id": "kimi", "name": "Kimi K2", "provider": "月之暗面"},
        {"id": "minimax", "name": "MiniMax M2.1", "provider": "MiniMax"}
    ]


def is_model_available(model_id: Optional[str]) -> bool:
    if not model_id:
        return False
    config = MODEL_CONFIGS.get(model_id)
    if not config:
        return False
    return bool(config.get("key"))


def resolve_available_model(preferred: Optional[str]) -> str:
    if preferred in MODEL_CONFIGS and is_model_available(preferred):
        return preferred

    for model_id, config in MODEL_CONFIGS.items():
        if config.get("key"):
            return model_id

    if preferred in MODEL_CONFIGS:
        return preferred

    return DEFAULT_MODEL
