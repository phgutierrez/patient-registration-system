import uvicorn

from src.core.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run('src.main:app', host=settings.host, port=settings.port)


if __name__ == '__main__':
    main()
