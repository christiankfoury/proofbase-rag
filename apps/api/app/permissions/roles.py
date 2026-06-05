CANONICAL_ROLES = {
    "Employee",
    "Sales Representative",
    "Manager",
    "HR Admin",
    "IT Admin",
}


def role_variants(user_role: str) -> list[str]:
    aliases = {
        "IT Admin": ["IT Admin", "IT/Admin"],
        "IT/Admin": ["IT/Admin", "IT Admin"],
    }
    return aliases.get(user_role, [user_role])

