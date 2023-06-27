import logging
from typing import Any, Dict, List, Optional

from collections.abc import MutableMapping

from ml_metadata import proto
from ml_metadata.metadata_store import metadata_store
from ml_metadata.proto.metadata_store_pb2 import MetadataStoreClientConfig, Event


# https://stackoverflow.com/a/6027615
def flatten(dictionary, parent_key='', separator=':'):
    items = []
    for key, value in dictionary.items():
        new_key = parent_key + separator + key if parent_key else key
        if isinstance(value, MutableMapping):
            items.extend(flatten(value, new_key, separator=separator).items())
        else:
            items.append((new_key, value))
    return dict(items)


def create_metadata_client() -> metadata_store.MetadataStore:
    metadata_service_host = 'metadata-grpc-service.kubeflow'
    metadata_service_port = 8080

    mlmd_connection_config = MetadataStoreClientConfig(
        host=metadata_service_host,
        port=metadata_service_port
    )
    return metadata_store.MetadataStore(mlmd_connection_config)


def extract_custom_properties(custom_properties) -> List[Dict[str, Any]]:
    output = []
    for prop, value in custom_properties.items():
        if prop == 'display_name':
            continue

        fields = value.ListFields()
        field_type, value = fields[0]
        output.append({
            'name': prop,
            'type': field_type.name,
            'value': value
        })
    return output


def transform_scalar_metrics_flat(metrics: Dict[str, Any]):
    flat_metrics = flatten(metrics, separator=':')

    output = {}
    for key, artefact in flat_metrics.items():
        for metric in artefact:
            output[f'{key}:{metric.get("name")}'] = metric.get('value')
    return output


def get_context(
        logger: logging.Logger,
        mlmd_store: metadata_store.MetadataStore,
        run_id: str
) -> Optional[proto.Context]:
    logger.debug(f'Getting metadata context for run_id {run_id}.')
    return mlmd_store.get_context_by_type_and_name(
        context_name=run_id,
        type_name='system.PipelineRun'
    )


def get_namespace(context: proto.Context) -> Optional[str]:
    namespace_property = context.custom_properties.get('namespace', None)
    return None if namespace_property is None else namespace_property.string_value


def get_scalar_metrics(
        logger: logging.Logger,
        mlmd_store: metadata_store.MetadataStore,
        context: proto.Context
) -> Dict[str, Any]:

    logger.debug(f'Getting artifact with context id: {context.id}.')
    artifacts = mlmd_store.get_artifacts_by_context(context_id=context.id)
    executions = mlmd_store.get_executions_by_context(context_id=context.id)
    events = mlmd_store.get_events_by_execution_ids(execution_ids=[execution.id for execution in executions])

    logger.debug(f'Found {len(artifacts)} artifacts.')

    metrics = {}

    artifacts_map = {artifact.id: artifact for artifact in artifacts}

    for execution in executions:
        execution_events = [event for event in events if event.execution_id == execution.id and event.type == Event.Type.OUTPUT]

        if len(execution_events) == 0:
            continue

        display_name = execution.custom_properties.get('display_name', None)
        if display_name is None:
            continue
        display_name = display_name.string_value

        execution_metrics = {}

        for event in execution_events:
            artifact = artifacts_map.get(event.artifact_id)
            artifact_name = artifact.custom_properties.get('display_name', None)
            if artifact_name is None:
                continue
            artifact_name = artifact_name.string_value

            custom_properties = extract_custom_properties(artifact.custom_properties)
            if len(custom_properties) > 0:
                execution_metrics[artifact_name] = custom_properties

        if len(execution_metrics) > 0:
            metrics[display_name] = execution_metrics

    return metrics
