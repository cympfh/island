.PHONY: default server dataset dataset-works dataset-reviews

default:
	cat Makefile

server:
	OPENBLAS_NUM_THREADS=1 uvicorn main:app --reload --port 8080

dataset: dataset-works dataset-reviews

dataset-works:
	bash ./fetch.sh works

dataset-reviews:
	bash ./fetch.sh reviews
