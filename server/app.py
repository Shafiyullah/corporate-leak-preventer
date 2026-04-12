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

from pii_redactor.models import PiiRedactorAction, PiiRedactorObservation
from pii_redactor.server.pii_redactor_environment import PiiRedactorEnvironment

# Create the app with web interface and README integration
app = create_app(
    PiiRedactorEnvironment,  # type: ignore
    PiiRedactorAction,       # type: ignore
    PiiRedactorObservation,  # type: ignore
    env_name="pii_redactor",
    max_concurrent_envs=1,
)


def main():
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 7860)) # Use HF's port if available, else 7860
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()