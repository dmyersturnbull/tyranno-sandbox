# Helm usage

Refer to the [Helm documentation](https://helm.sh/docs) for more info.

## Example usage

<!-- ::tyranno:: ```bash -->
<!-- ::tyranno:: helm repo add $<<project.name>> $<<project.urls.Source}} -->
<!-- ::tyranno:: helm repo update $<<project.name>> -->

```bash
helm repo add tyranno-sandbox https://github.com/dmyersturnbull/tyranno-sandbox
helm repo update tyranno-sandbox
```

<!-- ::tyranno:: After, simply `helm repo update $<<project.name>>` -->

After, simply `helm repo update tyranno-sandbox`
is sufficient to fetch the latest package versions.

<!-- :tyranno:: Run `helm search repo $<<project.name>>` -->

Run `helm search repo tyranno-sandbox`
to see the charts.

To install the main chart:

<!-- ::tyranno:: ```bash -->
<!-- ::tyranno:: helm install $<<project.name>> $<<project.name>>/$<<project.name>> -->

```bash
helm install tyranno-sandbox tyranno-sandbox/tyranno-sandbox
```

To uninstall the chart:

<!-- ::tyranno:: ```bash -->
<!-- ::tyranno:: helm delete $<<project.name>> $<<project.name>>/$<<project.name>> -->

```bash
helm delete tyranno-sandbox/tyranno-sandbox
```
