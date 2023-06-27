from typing import Union
from ml_metadata.metadata_store import metadata_store
from typing_extensions import Annotated
from fastapi import FastAPI, Header, HTTPException
from metrics import create_metadata_client, get_context, get_namespace, get_scalar_metrics
import os
import logging

app = FastAPI()
logger = logging.getLogger('scalar-metrics')

USER_ID_HEADER = os.getenv("USER_ID_HEADER")
GROUPS_HEADER = os.getenv("GROUPS_HEADER")

_mlmd_store: Union[metadata_store.MetadataStore, None] = None


def get_mlmd_store():
    global _mlmd_store
    if _mlmd_store is None:
        _mlmd_store = create_metadata_client()
    return _mlmd_store


@app.get("/health")
async def health():
    return {'message': 'ok'}


@app.get("/{run_id}")
async def get_metrics_by_run_id(
        run_id: str,
        user_id: Annotated[Union[str, None], Header(alias=USER_ID_HEADER)] = None,
        user_groups: Annotated[Union[str, None], Header(alias=GROUPS_HEADER)] = None
):
    context = get_context(
        logger=logger,
        mlmd_store=get_mlmd_store(),
        run_id=run_id
    )

    if context is None:
        raise HTTPException(status_code=404, detail="Context not found.")

    namespace = get_namespace(context)

    logger.info(f'Found context with namespace custom_properties: {namespace}')

    # TODO: check permission to access metrics

    return get_scalar_metrics(
        logger=logger,
        mlmd_store=get_mlmd_store(),
        context=context
    )
