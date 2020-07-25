.PHONY: default dataset processing

default:
	cat Makefile

server:
	OPENBLAS_NUM_THREADS=1 uvicorn main:app --reload --port 8080

dataset:
	bash ./fetch.sh > anime.json
