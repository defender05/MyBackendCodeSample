from api.services.user_service import UserService
from loguru import logger as log


async def get_all_users(limit: int = 500):
    db_users = []
    offset = 0

    while True:
        try:
            users = await UserService.get_users(
                order_by='tg_id',
                limit=limit,
                offset=offset
            )
        except Exception as e:
            log.error(f"Error fetching users: {e}")
            break

        if users is None or len(users) == 0:
            break
        else:
            db_users.extend(users)
            offset += limit

    return db_users
