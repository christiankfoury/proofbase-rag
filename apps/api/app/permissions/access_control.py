from apps.api.app.permissions.roles import role_variants
from apps.api.app.retrieval.types import RetrievedChunk


def sensitivity_from_restricted(restricted: bool) -> str:
    return "restricted" if restricted else "internal"


def role_can_access(access_roles: list[str] | tuple[str, ...], user_role: str) -> bool:
    allowed = set(access_roles)
    return any(role in allowed for role in role_variants(user_role))


def unauthorized_chunks(chunks: list[RetrievedChunk], user_role: str) -> list[RetrievedChunk]:
    return [chunk for chunk in chunks if not role_can_access(chunk.access_roles, user_role)]


def unauthorized_chunks_reached_generation(chunks: list[RetrievedChunk], user_role: str) -> bool:
    return bool(unauthorized_chunks(chunks, user_role))

