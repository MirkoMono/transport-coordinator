import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Production(Base):
    __tablename__ = "productions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    shoot_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    depot_location = mapped_column(Geography(geometry_type="POINT", srid=4326))
    call_time: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    runs: Mapped[list["OptimizationRun"]] = relationship(back_populates="production")


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text)
    location = mapped_column(Geography(geometry_type="POINT", srid=4326))
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OptimizationRun(Base):
    __tablename__ = "optimization_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    production_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("productions.id")
    )
    solver_status: Mapped[str] = mapped_column(String(64), nullable=False)
    total_distance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    input_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    production: Mapped[Production | None] = relationship(back_populates="runs")
    routes: Mapped[list["SavedRoute"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class SavedRoute(Base):
    __tablename__ = "saved_routes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("optimization_runs.id"), nullable=False
    )
    vehicle_id: Mapped[str] = mapped_column(String(64), nullable=False)
    vehicle_name: Mapped[str] = mapped_column(String(128), nullable=False)
    driver_name: Mapped[str] = mapped_column(String(128), default="")
    total_distance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    run: Mapped[OptimizationRun] = relationship(back_populates="routes")
    stops: Mapped[list["SavedRouteStop"]] = relationship(
        back_populates="route", cascade="all, delete-orphan", order_by="SavedRouteStop.sequence"
    )


class SavedRouteStop(Base):
    __tablename__ = "saved_route_stops"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("saved_routes.id"), nullable=False
    )
    node_id: Mapped[str] = mapped_column(String(64), nullable=False)
    person_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    eta_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    address: Mapped[str] = mapped_column(Text, default="")
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delay_minutes: Mapped[int | None] = mapped_column(Integer)
    delay_note: Mapped[str | None] = mapped_column(Text, default="")

    route: Mapped[SavedRoute] = relationship(back_populates="stops")
