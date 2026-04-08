# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FastAPI application for the Pii Redactor Environment.
"""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv is required for the web interface. Install dependencies with '\n    uv sync\n'"
    ) from e

try:
    from ..models import PiiRedactorAction, PiiRedactorObservation
    from .pii_redactor_environment import PiiRedactorEnvironment
except ModuleNotFoundError:
    from models import PiiRedactorAction, PiiRedactorObservation
    from server.pii_redactor_environment import PiiRedactorEnvironment


# Create the app with web interface and README integration
app = create_app(
    PiiRedactorEnvironment,  # type: ignore
    PiiRedactorAction,       # type: ignore
    PiiRedactorObservation,  # type: ignore
    env_name="pii_redactor",
    max_concurrent_envs=1,
)


def main(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()