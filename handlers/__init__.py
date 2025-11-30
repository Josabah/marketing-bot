from aiogram import Router

from . import start, callbacks, user_messages, staff, join_requests

router = Router()

router.include_router(start.router)
router.include_router(callbacks.router)
router.include_router(user_messages.router)
router.include_router(staff.router)
router.include_router(join_requests.router)
