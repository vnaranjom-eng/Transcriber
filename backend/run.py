import os

import uvicorn


def main():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info")
    uvicorn.run("backend.app:app", host=host, port=port, log_level=log_level, reload=False)


if __name__ == "__main__":
    main()

