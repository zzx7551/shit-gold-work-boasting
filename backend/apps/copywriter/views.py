import json
import os
from pathlib import Path
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

    payload = json.dumps(
        {
            "model": model,
            "messages": build_messages(raw_text, mode),
            "temperature": float(os.getenv("AI_TEMPERATURE", "0.8")),
            "top_p": 0.92,
            "max_tokens": int(os.getenv("AI_MAX_TOKENS", "650")),
            "stream": False,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(api_url, data=payload, headers=headers, method="POST")
    try:
        timeout = int(os.getenv("AI_TIMEOUT_SECONDS", "30"))
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return None

    content = extract_model_content(data)
    if content:
        return {"content": clean_model_content(content), "provider": provider, "model": model}
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
        "改成专业、高价值、有业务贡献感的中文表达。"
        "必须根据原句灵活变化，禁止套模板，禁止编造公司、学历、证书、职位、项目规模、金额或具体数据。"
        "语言要像真人面试会说的话，高级但落地。"
    )
    user_prompt = (
        f"场景：{scene}\n"
        f"原始大白话：{raw_text}\n\n"
        "只输出 3 部分：\n"
        "1. 高级改写：一段可直接复制的高档表达，80-140 字。\n"
        "2. 面试展开：一段自然口头回答，120-220 字。\n"
        "3. 可替换金句：3 条短句，每条不超过 35 字。\n\n"
        "不要输出“包装关键词”。不要固定使用“强执行与结果交付能力、信息结构化、推进闭环”等套话。"
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


def clean_model_content(content):
    markers = ("4. 包装关键词", "4.包装关键词", "四、包装关键词", "包装关键词：", "包装关键词:")
    cleaned = content.strip()
    for marker in markers:
        index = cleaned.find(marker)
        if index != -1:
            cleaned = cleaned[:index].rstrip()
    return cleaned


def build_local_copy(raw_text, mode):
    if mode == "resume":
        return build_resume_copy(raw_text)
    return build_interview_copy(raw_text)
