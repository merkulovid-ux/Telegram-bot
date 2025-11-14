from aiogram import Router
from . import common, llm_commands, admin, kb, feedback
from middlewares.subscription import CheckSubscription

# Применяем middleware к защищенным роутерам
kb.router.message.middleware(CheckSubscription())
llm_commands.router.message.middleware(CheckSubscription())

# Создаем и экспортируем главный роутер
router = Router()
router.include_router(admin.router)
router.include_router(kb.router)
router.include_router(feedback.router)
router.include_router(common.router)
router.include_router(llm_commands.router)