# In-memory conversation store keyed by conversationId.
# Lives as long as the server process — resets on restart.
# Swap for a Redis/DB-backed store later without changing callers.
_store: dict = {}


def get_history(conversation_id: str) -> list:
    return _store.get(conversation_id, [])


def save_message(conversation_id: str, role: str, content: str) -> None:
    if conversation_id not in _store:
        _store[conversation_id] = []
    _store[conversation_id].append({"role": role, "content": content})
