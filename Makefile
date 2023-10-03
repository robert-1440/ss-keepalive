PYTHON ?= python3

PYTHON_BASE_DIR ?= ~/PycharmProjects

BUILDER_DIR ?= $(PYTHON_BASE_DIR)/terraform-builder

BUILDER_CMD ?= $(PYTHON) $(BUILDER_DIR)/builder/builder.py

REGION ?= us-west-1

AWS_PROFILE ?= MyRepStudio

WORKSPACE ?= default
PROJECT ?= ss-keepalive
TERRAFORM_DIR ?= terraform
GATEWAY_DOMAIN_NAME = null
NO_GATEWAY_DOMAIN = true
BT_ARGS =


MAKE_TERRAFORM=make PROJECT=$(PROJECT) REGION=$(REGION) AWS_PROFILE=$(AWS_PROFILE) TERRAFORM_DIR=$(TERRAFORM_DIR) -f InfraMakefile

# INSTANCE_ID := $$($(PYTHON) archiver.py --uuid)
INSTANCE_ID := $(VERSION)

OUR_DIR=${PWD}

OUTPUT_PATH = .


DIST=dist/

TARGET_FILE=$(DIST)ss-keepalive.zip

all: all-tests

tests: all-tests

all-tests:
	@$(PYTHON) tests/run_tests.py --cov

build: package bt layer

build-and-push bp: build apply

layer: $(DIST)layer.zip

login-aws:
	@aws ecr get-login-password --region ${ECR_REGION} | docker login ${AWS_REPOSITORY} -u AWS --password-stdin

package: all-tests
	@python3 archiver.py $(TARGET_FILE)

fast-package fp:
	@python3 archiver.py $(TARGET_FILE)

#
# Here we are building the layer.zip file we will deploy, using the Amazon python docker image.
#
# It holds all third-party packages we need.
# This helps us avoid creating the lambda as an image deployment.
#
$(DIST)layer.zip: Dockerfile
	@docker rm -f build-archives
	@docker build -t build-py-targets-image .
	@docker create -it --name build-archives build-py-targets-image bash
	@docker cp build-archives:/var/task/python ./dist/python
	@docker rm -f build-archives
	@cd $(DIST) ; zip -r layer.zip python


build-terraform bt:
	 @$(BUILDER_CMD) --var region=$(REGION) \
			--var region-var=aws_region \
			--var project=$(PROJECT) --create --path $(OUTPUT_PATH) \
			--var gatewayDomainName=$(GATEWAY_DOMAIN_NAME) \
			--var noGatewayDomain=$(NO_GATEWAY_DOMAIN) \
			--var lambda-zip-file=$(TARGET_FILE) \
			--var layer-zip-file=$(DIST)layer.zip \
			--terraform-folder $(TERRAFORM_DIR) \
			$(BT_ARGS) \
			--aws ./infra/src
clean:
	@rm -fr $(DIST) ; mkdir $(DIST)

init:
	@$(MAKE_TERRAFORM) init

plan:
	@$(MAKE_TERRAFORM) plan

apply:
	@$(MAKE_TERRAFORM) apply

destroy:
	@$(MAKE_TERRAFORM) destroy

