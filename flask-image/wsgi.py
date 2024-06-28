# from waitress import serve
from app import create_app
import os
from dotenv import load_dotenv

load_dotenv()

print(f'ENVIRONMENT: {os.environ["ENVIRONMENT"]}')

app = create_app(os.environ["ENVIRONMENT"])
