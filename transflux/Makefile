REGISTRY := zot.lan
IMAGE    := homereef-transflux
TAG      := latest

# Paths
ROOT     := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
VENV     := $(ROOT).venv
APP_REQS := $(ROOT)app/requirements.txt
PIP      := $(VENV)/bin/pip

.PHONY: venv dev release clean build push deploy k8s-apply

# --- Development ---

venv: $(VENV)/bin/activate

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install -q --upgrade pip

dev: venv
	$(PIP) install -r $(APP_REQS)

release: venv
	$(PIP) install -r $(APP_REQS)

clean:
	rm -rf $(VENV)

# --- Container ---

build:
	podman build -f containerfile/homereef-transflux -t $(REGISTRY)/$(IMAGE):$(TAG) app

push: build
	podman push --tls-verify=false $(REGISTRY)/$(IMAGE):$(TAG)

deploy: push
	kubectl rollout restart deployment/homereef-transflux -n kube-idle
	kubectl rollout status deployment/homereef-transflux -n kube-idle

k8s-apply:
	kubectl apply -k deploy/k8s/overlays/homelab
