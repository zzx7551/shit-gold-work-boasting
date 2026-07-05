import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .resume_pdf import build_resume_pdf
from .transformer import build_interview_copy, build_resume_copy


PROJECT_ROOT = Path(__file__).resolve().parents[3]


@require_GET
def health_check(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "copywriter",
            "message": "Django API is running.",
        }
    )


@csrf_exempt
@require_POST
def transform_text(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    raw_text = str(payload.get("text", "")).strip()
    mode = str(payload.get("mode", "interview")).strip() or "interview"

    if not raw_text:
        return JsonResponse({"error": "Text is required."}, status=400)

    ai_result = call_external_ai(raw_text, mode)
    if ai_result:
        return JsonResponse(
            {
                "mode": mode,
                "input": raw_text,
                "result": ai_result["content"],
                "source": "external_ai",
                "provider": ai_result["provider"],
                "model": ai_result["model"],
            }
        )

    return JsonResponse(
        {
            "mode": mode,
            "input": raw_text,
            "result": build_local_copy(raw_text, mode),
            "source": "local_fallback",
            "provider": "local",
            "model": "semantic-transformer",
        }
    )


@csrf_exempt
@require_POST
def export_resume_pdf(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    resume = payload.get("resume") or {}
    if not isinstance(resume, dict):
        return JsonResponse({"error": "Resume must be an object."}, status=400)

    pdf_bytes = build_resume_pdf(resume)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="resume.pdf"'
    return response


def load_env_file(path):
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file(PROJECT_ROOT / ".env")


def call_external_ai(raw_text, mode):
    provider = os.getenv("AI_PROVIDER", "deepseek").strip() or "deepseek"
    api_key = (
        os.getenv("AI_API_KEY", "").strip()
        or os.getenv("AI_TEXT_MODEL_KEY", "").strip()
        or os.getenv("DEEPSEEK_API_KEY", "").strip()
    )
    if not api_key:
        return None

    base_url = os.getenv("AI_BASE_URL", "").strip()
    legacy_url = os.getenv("AI_TEXT_MODEL_URL", "").strip()
    model = os.getenv("AI_MODEL", "").strip()

    if not base_url and not legacy_url and provider == "deepseek":
        base_url = "https://api.deepseek.com"
    if not model and provider == "deepseek":
        model = "deepseek-v4-flash"
    if not model:
        model = "deepseek-v4-flash"

    api_url = normalize_chat_url(legacy_url or base_url)
    if not api_url:
        return None

    headers = {"Content-Type": "application/json"}
    headers["Authorization"] = f"Bearer {api_key}"

    max_tokens = int(os.getenv("AI_MAX_TOKENS", "260"))
    messages = build_messages(raw_text, mode)
    data = request_chat_completion(api_url, headers, model, messages, max_tokens)
    if not data:
        return None

    content = extract_model_content(data)
    finish_reason = extract_finish_reason(data)
    if content and should_continue_generation(content, finish_reason):
        continuation_messages = messages + [
            {"role": "assistant", "content": content},
            {
                "role": "user",
                "content": "上一条回答在中途停止了。请从断点处继续补完，只补完这一句话，不要重复前文。",
            },
        ]
        continuation_tokens = int(os.getenv("AI_CONTINUE_MAX_TOKENS", "700"))
        continuation_data = request_chat_completion(
            api_url, headers, model, continuation_messages, continuation_tokens
        )
        continuation = extract_model_content(continuation_data or {})
        if continuation:
            content = merge_continuation(content, continuation)

    if content:
        return {"content": clean_model_content(content), "provider": provider, "model": model}
    return None


def request_chat_completion(api_url, headers, model, messages, max_tokens):
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": float(os.getenv("AI_TEMPERATURE", "0.8")),
            "top_p": 0.92,
            "max_tokens": max_tokens,
            "stream": False,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(api_url, data=payload, headers=headers, method="POST")
    try:
        timeout = int(os.getenv("AI_TIMEOUT_SECONDS", "60"))
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return None


def normalize_chat_url(url):
    url = (url or "").rstrip("/")
    if not url:
        return ""
    if url.endswith("/chat/completions"):
        return url
    return f"{url}/chat/completions"


def build_messages(raw_text, mode):
    scene = "面试话术" if mode == "interview" else "简历表达"
    system_prompt = (
        "你是资深求职表达包装顾问。把普通、尴尬、不好听的大白话，"
        "改成专业、高价值、有业务贡献感的中文表达。必须根据原句灵活变化，禁止套模板。"
        "严禁编造任何原句没有的信息，包括公司、学历、证书、职位、项目规模、金额、奖项、成绩改善结果、具体数据、已经完成的成就。"
        "如果原句只提供了负面事实，只能把它解释为反思、调整意愿、补救方法、风险意识和成长心态，不能虚构后续已经成功。"
        "语言要像真人面试会说的话，高级但落地。只输出一句完整话术。"
    )
    user_prompt = (
        f"场景：{scene}\n"
        f"原始大白话：{raw_text}\n\n"
        "请只输出一句可直接复制到面试回答里的包装话术，70-120 字。"
        "不要编号，不要标题，不要分段，不要解释，不要输出“包装关键词”。"
        "句子必须完整，并以句号结尾。"
        "不要固定使用“强执行与结果交付能力、信息结构化、推进闭环”等套话。"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def extract_model_content(data):
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

    for key in ("result", "text", "content", "output"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def extract_finish_reason(data):
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        reason = choices[0].get("finish_reason")
        return str(reason or "").strip()
    return ""


def should_continue_generation(content, finish_reason):
    if finish_reason == "length":
        return True

    stripped = content.strip()
    if not stripped:
        return False
    if has_incomplete_bullet(stripped):
        return True
    return stripped[-1] not in "。！？.!?）)]」』”’"


def has_incomplete_bullet(content):
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith(("-", "·", "*")) and stripped[-1:] not in "。！？.!?）)]」』”’":
            return True
    return False


def merge_continuation(content, continuation):
    left = content.rstrip()
    right = continuation.strip()
    if not right:
        return left
    if right.startswith(left[-20:]):
        right = right[20:].lstrip()
    return f"{left}{right}" if left.endswith(("，", "、", "把", "将", "和")) else f"{left}\n{right}"


def clean_model_content(content):
    markers = ("4. 包装关键词", "4.包装关键词", "四、包装关键词", "包装关键词：", "包装关键词:")
    cleaned = content.strip()
    for marker in markers:
        index = cleaned.find(marker)
        if index != -1:
            cleaned = cleaned[:index].rstrip()
    cleaned = re.sub(r"^\s*(\d+[.、]|[一二三四]、)\s*", "", cleaned)
    cleaned = re.sub(r"^(高级改写|一句话版本|包装话术|面试话术)[:：]\s*", "", cleaned)
    return cleaned


def build_local_copy(raw_text, mode):
    if mode == "resume":
        return build_resume_copy(raw_text)
    return build_interview_copy(raw_text)
