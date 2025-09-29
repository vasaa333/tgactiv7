
import os

ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', '.env')
# The above constructs path that may be slightly off; better to search up for .env
def find_env_file():
    # search upwards for .env
    p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    candidates = [
        os.path.join(p, ".env"),
        os.path.join(os.path.dirname(p), ".env"),
        os.path.join(os.getcwd(), ".env")
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def write_env_var(key: str, value: str):
    env_path = find_env_file()
    if not env_path:
        # Can't find .env, try to write in current working dir
        env_path = ".env"
    # Read existing
    data = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip() or line.strip().startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                data[k.strip()] = v.strip().strip('"').strip("'")
    # Update
    data[key] = value
    # Write back (preserve comments lost)
    with open(env_path, "w", encoding="utf-8") as f:
        for k, v in data.items():
            f.write(f'{k}="{v}"\n')
    return env_path
