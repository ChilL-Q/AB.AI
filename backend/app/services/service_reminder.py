"""Service reminder engine — finds cars due for maintenance.

Checks each car's mileage and last service date against the team's
ServiceInterval definitions and returns a list of overdue/upcoming
services per car.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.car import Car
from app.db.models.client import Client
from app.db.models.service_interval import ServiceInterval

logger = logging.getLogger(__name__)

WARN_DAYS_BEFORE = 14
WARN_KM_BEFORE = 1000


async def get_due_services(
    team_id: uuid.UUID, session: AsyncSession
) -> list[dict]:
    """Return list of cars with services that are due or overdue.

    Each item: {
        "client_id": str,
        "client_name": str,
        "car": str (brand model year),
        "service_name": str,
        "reason": str ("overdue" or "due in N days/km"),
    }
    """
    intervals = (await session.execute(
        select(ServiceInterval).where(
            ServiceInterval.team_id == team_id,
            ServiceInterval.is_active.is_(True),
        )
    )).scalars().all()

    if not intervals:
        return []

    cars = (await session.execute(
        select(Car).join(Client, Car.client_id == Client.id).where(
            Client.team_id == team_id,
            Client.deleted_at.is_(None),
            Client.do_not_contact.is_(False),
        )
    )).scars().all()

    results = []
    now = datetime.now(UTC)

    for car in cars:
        client = await session.scalar(
            select(Client).where(Client.id == car.client_id)
        )
        if not client:
            continue

        car_label = f"{car.brand} {car.model} {car.year or ''}"

        for interval in intervals:
            due_reason = _check_due(car, interval, now)
            if due_reason:
                results.append({
                    "client_id": str(client.id),
                    "client_name": client.full_name,
                    "car": car_label,
                    "service_name": interval.name,
                    "reason": due_reason,
                })

    return results


def _check_due(car: Car, interval: ServiceInterval, now: datetime) -> str | None:
    """Check if a car is due for a specific service. Returns reason or None."""
    if interval.interval_unit == "km":
        if car.mileage is None or car.last_service_mileage is None:
            return None
        km_since = car.mileage - car.last_service_mileage
        km_remaining = interval.interval_value - km_since
        if km_remaining <= 0:
            return f"Пробег превышен на {abs(km_remaining)} км"
        if km_remaining <= WARN_KM_BEFORE:
            return f"Осталось {km_remaining} км до {interval.name}"

    elif interval.interval_unit in ("days", "months"):
        if car.last_service_at is None:
            return f"{interval.name} — никогда не проводилось"
        days_in_interval = interval.interval_value if interval.interval_unit == "days" else interval.interval_value * 30
        days_since = (now - car.last_service_at).days
        days_remaining = days_in_interval - days_since
        if days_remaining <= 0:
            return f"Просрочено на {abs(days_remaining)} дн. ({interval.name})"
        if days_remaining <= WARN_DAYS_BEFORE:
            return f"Через {days_remaining} дн. ({interval.name})"

    return None