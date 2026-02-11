.PHONY: install install-backend install-frontend install-platform dev dev-backend dev-frontend test test-platform lint lint-platform format package-lambda tf-init tf-plan tf-apply tf-destroy run-pipeline

# Python実行パス
PYTHON := cd backend && poetry run python
UVICORN := cd backend && poetry run uvicorn

install: install-backend install-frontend

install-backend:
	cd backend && poetry install

install-frontend:
	cd frontend && npm install

dev:
	@echo "バックエンド(8080)とフロントエンド(5173)を同時起動..."
	$(MAKE) dev-backend & $(MAKE) dev-frontend & wait

dev-backend:
	$(UVICORN) app.main:app --reload --port 8080

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && poetry run pytest tests/ -v

lint:
	cd backend && poetry run ruff check app/ tests/
	cd backend && poetry run ruff format --check app/ tests/
	cd backend && poetry run mypy app/

format:
	cd backend && poetry run ruff check --fix app/ tests/
	cd backend && poetry run ruff format app/ tests/

# ====================
# データプラットフォーム
# ====================

install-platform:
	cd data-platform && poetry install

test-platform:
	cd data-platform && poetry run pytest tests/ -v

lint-platform:
	cd data-platform && poetry run ruff check glue/ lambda/ tests/
	cd data-platform && poetry run ruff format --check glue/ lambda/ tests/

format-platform:
	cd data-platform && poetry run ruff check --fix glue/ lambda/ tests/
	cd data-platform && poetry run ruff format glue/ lambda/ tests/

package-lambda:
	@echo "Lambda Layer をビルド中..."
	mkdir -p terraform/.build
	docker run --rm --platform linux/arm64 \
		-v $(CURDIR)/data-platform/lambda/ingest:/var/task \
		-v $(CURDIR)/terraform/.build:/out \
		public.ecr.aws/lambda/python:3.12-arm64 \
		bash -c "pip install -r /var/task/requirements.txt -t /tmp/python && cd /tmp && zip -r /out/lambda_layer.zip python/"
	cd data-platform/lambda/ingest && zip -r ../../../terraform/.build/lambda_ingest.zip handler.py jquants_fetcher.py
	@echo "ビルド完了: terraform/.build/"

# ====================
# Terraform
# ====================

tf-init:
	cd terraform && terraform init

tf-plan:
	cd terraform && terraform plan

tf-apply:
	cd terraform && terraform apply

tf-destroy:
	cd terraform && terraform destroy

# ====================
# パイプライン手動実行
# ====================

run-pipeline:
	@echo "Step Functions パイプラインを手動実行中..."
	aws stepfunctions start-execution \
		--state-machine-arn $$(cd terraform && terraform output -raw step_functions_arn) \
		--region ap-northeast-1
