"""Run the CodeLoop server: `uv run python -m codeloop` (or `uvicorn codeloop.api.app:create_app --factory`)."""

import logging
import os

import uvicorn


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    uvicorn.run(
        "codeloop.api.app:create_app",
        factory=True,
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
        ws_max_size=2**20,
    )


if __name__ == "__main__":
    main()
