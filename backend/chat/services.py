import hashlib

from accounts.models import User


def guest_key(session):
    if not session.session_key:
        return ""
    return hashlib.sha256(session.session_key.encode()).hexdigest()


def can_access(conversation, user, key=""):
    if user.is_authenticated:
        if not user.is_active:
            return False
        if user.role == User.Role.SUPPORT_AGENT:
            return True
        return (
            user.role == User.Role.CUSTOMER
            and conversation.user_id == user.pk
        )

    return bool(
        key
        and conversation.user_id is None
        and conversation.guest_key == key
    )


def message_data(message):
    return {
        "id": message.pk,
        "conversation_id": str(message.conversation_id),
        "sender_role": message.sender_role,
        "text": message.text,
        "created_at": message.created_at.isoformat(),
    }