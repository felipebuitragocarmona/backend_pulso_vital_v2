from typing import List, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class PatientORM(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fullName: Mapped[str] = mapped_column(String(150), nullable=False)
    birthDate: Mapped[str] = mapped_column(String(30), nullable=False)
    createdAt: Mapped[str] = mapped_column(String(40), nullable=False)
    updatedAt: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)

    ecgs: Mapped[List["EcgORM"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class EcgORM(Base):
    __tablename__ = "ecgs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patientId: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    registeredAt: Mapped[str] = mapped_column(String(40), nullable=False)
    pdfUrl: Mapped[str] = mapped_column(String(500), nullable=False)
    originalFilename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    uploadedAt: Mapped[str] = mapped_column(String(40), nullable=False)

    patient: Mapped[PatientORM] = relationship(back_populates="ecgs")
