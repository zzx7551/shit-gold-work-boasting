import re


DIMENSIONS = [
    {
        "name": "快速学习",
        "signals": ("不会", "没经验", "不懂", "新手", "小白", "刚学", "啥也", "什么也"),
        "ability": "快速学习与知识迁移能力",
        "method": "通过高频反馈、案例拆解和复盘迭代快速补齐认知差距",
        "value": "缩短从陌生任务到稳定产出的适应周期",
        "keywords": ("学习曲线", "认知升级", "可塑性", "成长潜力"),
    },
    {
        "name": "执行落地",
        "signals": ("做", "干", "弄", "处理", "完成", "执行", "跑腿", "打杂", "杂活"),
        "ability": "强执行与结果交付能力",
        "method": "将模糊事项拆解为可执行动作，并持续推进到闭环",
        "value": "提升任务落地确定性，减少协作中的等待和损耗",
        "keywords": ("执行闭环", "任务拆解", "结果导向", "交付意识"),
    },
    {
        "name": "协同推进",
        "signals": ("催", "盯", "跟进", "协调", "沟通", "对接", "拉群", "开会", "同步"),
        "ability": "跨角色沟通与项目推进能力",
        "method": "通过节点提醒、风险暴露和信息同步维持协作节奏",
        "value": "保障多人协作场景下的进度透明和责任清晰",
        "keywords": ("进度管理", "风险前置", "跨部门协同", "节点推进"),
    },
    {
        "name": "信息结构化",
        "signals": ("表格", "excel", "ppt", "文档", "材料", "整理", "汇总", "记录", "会议纪要"),
        "ability": "信息结构化与表达沉淀能力",
        "method": "把零散信息转化为清晰、可复用、可决策的资料资产",
        "value": "降低团队理解成本，提升信息传递和后续复用效率",
        "keywords": ("信息资产化", "结构化表达", "文档沉淀", "复用机制"),
    },
    {
        "name": "数据意识",
        "signals": ("数据", "统计", "分析", "报表", "指标", "转化", "增长", "复盘"),
        "ability": "数据敏感度与业务分析能力",
        "method": "围绕指标变化定位问题，并用数据反馈校准执行方向",
        "value": "让工作从经验驱动升级为可衡量、可优化的过程管理",
        "keywords": ("指标意识", "数据复盘", "问题定位", "策略校准"),
    },
    {
        "name": "责任担当",
        "signals": ("背锅", "救火", "加班", "扛", "兜底", "临时", "紧急", "没人管"),
        "ability": "复杂场景下的责任意识和稳定性",
        "method": "在不确定任务中主动补位，优先保障关键结果不掉线",
        "value": "提升团队在突发场景下的响应速度和交付韧性",
        "keywords": ("主动补位", "抗压能力", "应急响应", "稳定交付"),
    },
    {
        "name": "用户理解",
        "signals": ("客户", "用户", "老板", "领导", "同事", "需求", "反馈", "投诉"),
        "ability": "需求理解与关系维护能力",
        "method": "识别不同角色的真实诉求，并转化为可执行的沟通方案",
        "value": "提升沟通满意度，减少需求偏差带来的返工",
        "keywords": ("需求洞察", "关系维护", "预期管理", "沟通转译"),
    },
]

FILLER_PATTERNS = (
    r"我就是",
    r"我只是",
    r"其实",
    r"感觉",
    r"好像",
    r"可能",
    r"大概",
    r"啥也",
    r"什么也",
)

EUPHEMISM_REPLACEMENTS = (
    ("啥也不会", "从零接触新任务"),
    ("什么也不会", "从零接触新任务"),
    ("我不会", "我正在快速补齐相关能力"),
    ("不会", "处于快速学习阶段"),
    ("打杂", "多线程事务支持"),
    ("杂活", "综合事务支持"),
    ("跑腿", "现场执行与资源协调"),
    ("催别人", "推进相关方按节点交付"),
    ("催", "节点推进"),
    ("背锅", "复杂问题兜底"),
    ("救火", "突发问题响应"),
    ("加班", "关键节点保障"),
)


def build_interview_copy(raw_text):
    normalized = normalize_text(raw_text)
    selected = select_dimensions(normalized)
    topic = extract_topic(normalized, selected)

    primary = selected[0]
    secondary = selected[1] if len(selected) > 1 else selected[0]
    third = selected[2] if len(selected) > 2 else selected[-1]

    keywords = unique_keywords(selected)
    ability_line = join_cn([item["ability"] for item in selected[:3]])
    method_lines = numbered_lines([item["method"] for item in selected[:3]])
    value_lines = numbered_lines([item["value"] for item in selected[:3]])

    return (
        f"高阶表达：围绕“{topic}”，我体现出的不是单一事务处理能力，而是{ability_line}。"
        f"我习惯先理解目标，再把问题拆成可推进、可反馈、可复盘的执行路径，从而{primary['value']}。\n\n"
        f"面试展开：这类经历看似基础，但本质上要求候选人具备{secondary['ability']}。"
        f"我的处理方式可以拆成三层：\n{method_lines}\n\n"
        f"价值呈现：\n{value_lines}\n"
        f"因此，我的价值不只是完成动作，而是把普通任务转化为可推进、可衡量、可复用的工作成果。\n\n"
        f"技术感关键词：{keywords}。\n\n"
        f"一句话版本：我具备{primary['ability']}，能够在{third['name']}相关场景中主动识别问题、推进闭环，并沉淀可复用的方法。"
    )


def build_resume_copy(raw_text):
    normalized = normalize_text(raw_text)
    selected = select_dimensions(normalized)
    topic = extract_topic(normalized, selected)
    keywords = unique_keywords(selected)

    return (
        f"简历表达：负责“{topic}”相关工作的执行推进与过程优化，"
        f"围绕{join_cn([item['name'] for item in selected[:3]])}建立清晰的任务拆解和反馈闭环，"
        f"沉淀{keywords}等方法，提升协作效率、信息透明度和结果交付稳定性。"
    )


def normalize_text(raw_text):
    text = str(raw_text or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text[:240]


def extract_topic(text, dimensions=None):
    topic = text
    replacement_hits = 0
    for pattern in FILLER_PATTERNS:
        topic = re.sub(pattern, "", topic)
    for source, target in EUPHEMISM_REPLACEMENTS:
        if source in topic:
            replacement_hits += 1
            topic = topic.replace(source, f" {target} ")
    topic = re.sub(r"(我|每天|经常|就是|只是|主要|负责|帮忙|顺便|相关)+$", "", topic)
    topic = re.sub(r"^(我|每天|经常|就是|只是|主要|负责|帮忙|顺便)+", "", topic)
    topic = re.sub(r"\s+", "、", topic)
    topic = re.sub(r"、+", "、", topic)
    topic = topic.replace("交付、交", "交付")
    topic = topic.strip(" ，。！？、；;,.!?")
    if dimensions and (replacement_hits >= 2 or len(topic) < 6):
        names = "、".join(item["name"] for item in dimensions[:2])
        return f"{names}相关经历"
    return topic or text or "这段经历"


def select_dimensions(text):
    scored = []
    lower_text = text.lower()
    for index, dimension in enumerate(DIMENSIONS):
        score = 0
        for signal in dimension["signals"]:
            target = lower_text if signal.isascii() else text
            if signal in target:
                score += 2 + min(len(signal), 4) * 0.2
        if score:
            scored.append((score, -index, dimension))

    if not scored:
        scored = [
            (1.0, 0, DIMENSIONS[1]),
            (0.9, -1, DIMENSIONS[0]),
            (0.8, -2, DIMENSIONS[3]),
        ]

    scored.sort(reverse=True)
    selected = [item[2] for item in scored[:3]]
    for fallback in DIMENSIONS:
        if len(selected) >= 3:
            break
        if fallback not in selected:
            selected.append(fallback)
    return selected


def unique_keywords(dimensions):
    words = []
    for dimension in dimensions:
        for keyword in dimension["keywords"]:
            if keyword not in words:
                words.append(keyword)
    return " / ".join(words[:8])


def join_cn(items):
    cleaned = [item for item in items if item]
    if len(cleaned) <= 1:
        return cleaned[0] if cleaned else ""
    if len(cleaned) == 2:
        return "和".join(cleaned)
    return "、".join(cleaned[:-1]) + "和" + cleaned[-1]


def numbered_lines(items):
    return "\n".join(f"{index}. {item}。" for index, item in enumerate(items, start=1))
