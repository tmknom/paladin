import json
import os


def greet() -> str:
    return json.dumps({"message": os.getcwd()})
