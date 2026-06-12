"""Default template seeds.

Run once at startup or via a management command to populate the templates table.
Templates are owned by a system user (user_id=None is not possible due to FK
constraints, so callers must pass a seed_user_id).
"""
import uuid

TEMPLATES = [
    {
        "name": "YouTube 댓글 자동 관리",
        "description": "스팸 댓글 자동 숨김 + 질문 댓글에 AI 답글 초안 작성",
        "role_type": "youtube_moderator",
        "system_prompt": (
            "당신은 YouTube 채널 댓글 관리 비서입니다. "
            "스팸이나 부적절한 댓글은 숨기고, 진지한 질문에는 친절하고 정확한 답글 초안을 작성합니다."
        ),
        "config": {
            "required_action_types": [
                "youtube.comment.list",
                "youtube.comment.reply",
                "youtube.comment.hide",
            ],
            "max_comments_per_run": 50,
        },
    },
    {
        "name": "Gmail 이메일 자동 분류 & 답장 초안",
        "description": "미확인 메일 분류 후 긴급/질문 메일에 자동 답장 초안 작성",
        "role_type": "gmail_responder",
        "system_prompt": (
            "당신은 이메일 관리 비서입니다. "
            "긴급하거나 답변이 필요한 이메일을 식별하고, 정중하고 전문적인 답장 초안을 작성합니다."
        ),
        "config": {
            "required_action_types": [
                "gmail.message.list",
                "gmail.draft.create",
                "gmail.message.label",
            ],
            "max_messages_per_run": 20,
        },
    },
    {
        "name": "Google Drive 문서 요약",
        "description": "Drive 폴더의 새 문서를 읽고 요약 문서 자동 생성",
        "role_type": "drive_summarizer",
        "system_prompt": (
            "당신은 Google Drive 문서 요약 비서입니다. "
            "새로 추가된 문서를 읽고 핵심 내용을 한국어로 요약하여 새 문서로 저장합니다."
        ),
        "config": {
            "required_action_types": [
                "drive.file.list",
                "drive.file.read",
                "drive.document.create",
            ],
            "max_files_per_run": 10,
        },
    },
]


async def seed_default_templates(session, seed_user_id: uuid.UUID) -> None:
    """Insert default templates if they don't exist yet."""
    from sqlalchemy import select

    from app.models.assistant import Assistant

    for tpl in TEMPLATES:
        existing = await session.execute(
            select(Assistant).where(
                Assistant.name == tpl["name"],
                Assistant.is_template.is_(True),
            )
        )
        if existing.scalar_one_or_none():
            continue

        assistant = Assistant(
            user_id=seed_user_id,
            name=tpl["name"],
            description=tpl["description"],
            role_type=tpl["role_type"],
            system_prompt=tpl["system_prompt"],
            config=tpl["config"],
            is_active=False,
            is_template=True,
        )
        session.add(assistant)
