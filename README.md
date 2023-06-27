# kfp-metrics-collector

Single endpoint service to fetch [scalar metrics](https://www.kubeflow.org/docs/components/pipelines/v1/sdk/output-viewer/#scalar-metrics) of a kubeflow pipeline run.

## Build

````shell
docker build -f Dockerfile .
````

## Deploy

Replace in `k8s/deployement.yaml` the {INSERT IMAGE} with the image you built.

## Usage

Make GET request on `https://{kubeflow-instance}/kfp-metrics-collector/{run-id}`.

### Example output

````json
{
    "node-a": {
        "artifact-a": [{
                "name": "result",
                "value": 8,
                "type": "integer_value"
            }
        ]
    },
    "node-b": {
        "artifact-b": [{
                "name": "result",
                "value": 8.5,
                "type": "double_value"
            }, {
                "name": "example",
                "value": 15,
                "type": "double_value"
            },
        ]
    },
}
````
