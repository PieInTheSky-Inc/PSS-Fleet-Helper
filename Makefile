.PHONY: check
check:
	uv run flake8 .
	
.PHONY: format
format:
	uv run autoflake .
	uv run isort .
	uv run black .

.PHONY: lock#
lock:
	uv export --format requirements.txt --no-dev --no-hashes --no-annotate --output-file requirements.txt
	uv export --format requirements.txt --no-hashes --no-annotate --output-file requirements_dev.txt

.PHONY: docker
docker:
	-docker stop container-pss-fleet-helper
	docker rm -f container-pss-fleet-helper
	docker image rm -f image-pss-fleet-helper:latest
	docker build -t image-pss-fleet-helper .
	docker run --env-file ./docker.env -d --name container-pss-fleet-helper -p 80:80 --add-host host.docker.internal:host-gateway image-pss-fleet-helper:latest