"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
import sys
import inspect
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def check_for_droop():
    # Get the current script's filename
    script_filename = __file__
    try:
        # Ensure the script's filename is not modified to an unexpected form by various environments
        source_code = inspect.getsource(upgrade)
        # Open and read the script's own source code
        if 'drop' in source_code:
            sys.stdout.write(f"this migration could result in data loss, have you verified the upgrade function [y/n]: ")
            choice = input().lower()
            if choice not in ['y', 'yes']:
                sys.stdout.write("Migration aborted.\n")
                sys.exit(0)
    except Exception as e:
        print(f"An error occurred while trying to read the script: {e}")

def upgrade():
    check_for_droop() # you can remove this once you have verified the functionality
    # common fix is op.execute('UPDATE table SET newname = oldname')
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}
