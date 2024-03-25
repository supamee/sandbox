#!/bin/bash
sudo apt install sqlite3
pip install sqlalchemy
python3 data1.py

sudo apt install alembic
alembic init alembic

#sed command to replace "sqlalchemy.url = driver://user:pass@localhost/dbname" with "sqlalchemy.url = sqlite:///example.db" in alembic.ini
sed -i 's/sqlalchemy.url = driver:\/\/user:pass@localhost\/dbname/sqlalchemy.url = sqlite:\/\/\/example.db/g' alembic.ini

# add the import statement to env.py
sed -i '1s/^/from data1 import Base\n/' alembic/env.py
# update target_metadata in env.py
sed -i 's/target_metadata = None/target_metadata = Base.metadata/g' alembic/env.py

alembic revision --autogenerate -m "Initial migration"

alembic upgrade head


# change the data1.py to add a new field


alembic revision --autogenerate -m "Describe your changes"
# this makes a file under ./alembic/versions/NUMBER_describe_your_changes.py

alembic upgrade head