# hetzner-aux-node-manager 

I wrote this operator for my custom setup of https://github.com/kube-hetzner/terraform-hcloud-kube-hetzner

As a simple kubernetes operator, it loops over nodes (all the kubernetes one + other VMs you can specify) and if needed it adds them to the required extra networks.
As a plus, it also enforces a firewall (or any number of them) to be always applied to all nodes.
If you manually remove a node from a network or from the firewall by mistake (for example in the Hetzner Web-UI), the operator kicks in and enforces the attachments again.

## Installation

You may want to:

1. Tweak the values in values-example.yaml and rename to values.yaml
2. Optionally review the chart with helm template .
2. Install with helm template . | kubectl apply -f

## See it in action
Follow the logs of the created container (the default deployment name is hetzner-aux-node-operator)
Then add a node to the kubernetes cluster or try to remove a node from a firewall or from a network, the operator should remediated in a few seconds to re-establish the correct condition
