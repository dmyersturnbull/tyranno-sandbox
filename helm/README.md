# Helm usage

Refer to the [Helm documentation](https://helm.sh/docs) for more info.

## Example usage

```bash
helm repo add tyranno-sandbox https://github.com/dmyersturnbull/tyranno-sandbox
helm repo update tyranno-sandbox
```

If you had already added this repo earlier, run `helm repo update` to retrieve the latest versions of the packages. You can then run `helm search repo mansunkuo-k8s-summit-2024` to see the charts.

To install the myapi chart:

    helm install tyranno-sandbox tyranno-sandbox/tyranno-sandbox

To uninstall the chart:

    helm delete mansunkuo-myapi
