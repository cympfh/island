.PHONY: default server dataset dataset-works dataset-reviews dataset-records

default:
	cat Makefile

server:
	OPENBLAS_NUM_THREADS=1 uvicorn main:app --reload --port 8080

dataset: dataset-works dataset-reviews dataset-records

dataset-works:
	bash ./fetch.sh works

dataset-reviews:
	bash ./fetch.sh reviews

dataset-records:
	bash ./fetch.sh records
