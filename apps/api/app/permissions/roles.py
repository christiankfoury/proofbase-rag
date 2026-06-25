CANONICAL_ROLES = {
    "Admin",
    "Employee",
    "Sales Representative",
    "Manager",
    "HR Admin",
    "IT Admin",
}


def role_variants(user_role: str) -> list[str]:
    aliases = {
        "Admin": ["Admin", "Employee", "Sales Representative", "Manager", "HR Admin", "IT Admin", "IT/Admin"],
        "IT Admin": ["IT Admin", "IT/Admin"],
        "IT/Admin": ["IT/Admin", "IT Admin"],
        "Knowledge Manager": ["Admin", "Employee", "Sales Representative", "Manager", "HR Admin", "IT Admin", "IT/Admin"],
    }
    return aliases.get(user_role, [user_role])
