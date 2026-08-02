ADMIN_IDS = [
    8119525298,
]

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS
