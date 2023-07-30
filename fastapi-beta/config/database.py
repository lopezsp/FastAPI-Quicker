import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

#sqlite_file_name = "./database.sqlite"
#base_dir = os.path.dirname(os.path.realpath(__file__))
load_dotenv()
database_user = os.environ.get('DATABASE_USER')
database_password = os.environ.get('DATABASE_PASSWORD')
database_id = os.environ.get('DATABASE_ID')

#database_url = f"sqlite:///{os.path.join(base_dir, sqlite_file_name)}"
database_url = f'postgresql://{database_user}:{database_password}@database-1.{database_id}.us-east-2.rds.amazonaws.com:5432/quickerdb'

engine = create_engine(database_url, echo=True)


Session = sessionmaker(bind=engine)

Base = declarative_base()