
from code_search import search_code


sample_files = {
    "app.py": (
        "def login(username, password):\n"
        "    validate_user(username)\n"
        "    return authenticate(password)\n"
    ),
    "database.py": (
        "def connect_database():\n"
        "    print('Connecting to database')\n"
    ),
}

results = search_code(sample_files, "login password")

for result in results:
    print(
        f"{result['path']}:{result['line_number']}: "
        f"{result['line']}"
    )
