"""Allow a dislike reaction on community posts."""

from collections.abc import Sequence

from alembic import op

revision: str = "0018_add_dislike_reaction"
down_revision: str | Sequence[str] | None = "0017_validate_movie_performance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("community_reactions") as batch_op:
        batch_op.drop_constraint("reaction_type_valid", type_="check")
        batch_op.create_check_constraint(
            "reaction_type_valid",
            "tipo IN ('curtir', 'amei', 'interessante', 'nao_curti')",
        )


def downgrade() -> None:
    op.execute("UPDATE community_reactions SET tipo = 'curtir' WHERE tipo = 'nao_curti'")
    with op.batch_alter_table("community_reactions") as batch_op:
        batch_op.drop_constraint("reaction_type_valid", type_="check")
        batch_op.create_check_constraint(
            "reaction_type_valid",
            "tipo IN ('curtir', 'amei', 'interessante')",
        )
