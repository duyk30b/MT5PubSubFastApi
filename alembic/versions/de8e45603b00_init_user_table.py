"""init user table

Revision ID: de8e45603b00
Revises:
Create Date: 2026-04-27 01:14:12.402748

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "de8e45603b00"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE TABLE "User" (
            "id" SERIAL NOT NULL, 
            "fullName" VARCHAR(255) NOT NULL, 
            "username" VARCHAR(50) NOT NULL, 
            "passwordHash" VARCHAR(255) NOT NULL, 
            "userType" INTEGER NOT NULL, 
            "isActive" INTEGER NOT NULL, 
            "createdAt" BIGINT NOT NULL, 
            "updatedAt" BIGINT NOT NULL, 
            PRIMARY KEY ("id")
        );
        CREATE INDEX "ix_User_id" ON "User" ("id");
        CREATE UNIQUE INDEX "ix_User_username" ON "User" ("username");

        INSERT INTO "User" ("fullName", "username", "passwordHash", "userType", "isActive", "createdAt", "updatedAt")
        VALUES ('Admin', 'admin', '$2b$12$9uxvRwWH4jhE0A9twcYynukTc9oBEopW4HMWi21ZCdGHn9inmvZu2',
                 0, 1, EXTRACT(EPOCH FROM NOW()), EXTRACT(EPOCH FROM NOW())
                );
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        """
        DROP TABLE IF EXISTS "User";
        """
    )
