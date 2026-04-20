from fastapi import APIRouter

from app.api.v1 import (
    ai_agent,
    analytics,
    auth,
    billing,
    campaigns,
    cars,
    clients,
    conversations,
    imports,
    messages,
    notifications,
    settings,
    teams,
    templates,
    users,
    visits,
    webhooks,
)

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/me", tags=["me"])
router.include_router(teams.router, prefix="/team", tags=["team"])
router.include_router(clients.router, prefix="/clients", tags=["clients"])
router.include_router(cars.router, prefix="/cars", tags=["cars"])
router.include_router(visits.router, prefix="/visits", tags=["visits"])
router.include_router(imports.router, prefix="/imports", tags=["imports"])
router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
router.include_router(templates.router, prefix="/templates", tags=["templates"])
router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
router.include_router(messages.router, prefix="/messages", tags=["messages"])
router.include_router(ai_agent.router, prefix="/ai-agent", tags=["ai-agent"])
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
router.include_router(billing.router, prefix="/billing", tags=["billing"])
router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
router.include_router(settings.router, prefix="/settings", tags=["settings"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
