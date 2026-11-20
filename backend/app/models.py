from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

class Line(Base):
    __tablename__ = "lines"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    color: Mapped[str] = mapped_column(String(50), nullable=False)

class StationLine(Base):
    __tablename__ = "station_lines"

    station_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("stations.id"), primary_key=True
    )
    line_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("lines.id"), primary_key=True
    )

class RideConnection(Base):
    __tablename__ = "ride_connections"
    __table_args__ = (
        UniqueConstraint(
            "start_station_id",
            "end_station_id",
            "line_id",
            name="uq_ride_connection_direction_line",
        ),
        CheckConstraint(
            "duration_seconds > 0",
            name="ck_ride_connection_duration_positive",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    start_station_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("stations.id"), nullable=False
    )
    end_station_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("stations.id"), nullable=False
    )
    line_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("lines.id"), nullable=False
    )
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)


class TransferEdge(Base):
    __tablename__ = "transfer_edges"
    __table_args__ = (
        CheckConstraint("duration_seconds > 0", name="ck_transfer_duration_positive"),
    )

    start_station_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("stations.id"), primary_key=True
    )
    end_station_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("stations.id"), primary_key=True
    )
    duration_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=420, server_default="420"
    )
    source: Mapped[str] = mapped_column(String(500), nullable=False)


class TransferOverride(Base):
    __tablename__ = "transfer_overrides"
    __table_args__ = (
        ForeignKeyConstraint(
            ["start_station_id", "end_station_id"],
            [
                "transfer_edges.start_station_id",
                "transfer_edges.end_station_id",
            ],
            name="fk_transfer_override_edge",
        ),
        CheckConstraint(
            "duration_seconds > 0",
            name="ck_transfer_override_duration_positive",
        ),
    )

    start_station_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    end_station_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(300), nullable=False)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("oidc_issuer", "oidc_subject", name="uq_user_oidc_identity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    oidc_issuer: Mapped[str] = mapped_column(String(255), nullable=False)
    oidc_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    display_name: Mapped[str | None] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SavedJourney(Base):
    __tablename__ = "saved_journeys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    origin_station_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("stations.id"), nullable=False
    )
    destination_station_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("stations.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SearchHistory(Base):
    __tablename__ = "search_history"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "origin_station_id",
            "destination_station_id",
            name="uq_search_history_user_station_pair",
        ),
        CheckConstraint("search_count > 0", name="ck_search_history_count_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    origin_station_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("stations.id"), nullable=False
    )
    destination_station_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("stations.id"), nullable=False
    )
    last_searched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    search_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class NetworkRevision(Base):
    __tablename__ = "network_revisions"

    revision: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(500), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    station_count: Mapped[int] = mapped_column(Integer, nullable=False)
    line_count: Mapped[int] = mapped_column(Integer, nullable=False)
    ride_connection_count: Mapped[int] = mapped_column(Integer, nullable=False)
    transfer_edge_count: Mapped[int] = mapped_column(Integer, nullable=False)

