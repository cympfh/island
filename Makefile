.PHONY: default server dataset dataset-works dataset-reviews dataset-records

PORT := 8087

default:
	cat Makefile

server:
	OPENBLAS_NUM_THREADS=1 uvicorn main:app \
		--log-config logging.yml \
		--use-colors \
		--host 0.0.0.0 \
		--port $(PORT) \

dev:
	OPENBLAS_NUM_THREADS=1 uvicorn main:app \
		--log-config logging.yml \
		--use-colors \
		--host 0.0.0.0 \
		--port $(PORT) \
		--reload

dataset: dataset-works dataset-reviews dataset-records

dataset-works:
	bash ./fetch.sh works

dataset-reviews:
	bash ./fetch.sh reviews

dataset-records:
	bash ./fetch.sh records

dataset-staffs:
	bash ./fetch.sh staffs
