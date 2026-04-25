from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader

_env = Environment(loader=FileSystemLoader("app/templates"), cache_size=0)
templates = Jinja2Templates(env=_env)