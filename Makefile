.PHONY: default server dataset dataset-works dataset-reviews dataset-records

PORT := 8087

default:
	cat Makefile

server:
	OPENBLAS_NUM_THREADS=1 uvicorn main:app \
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

dataset:
	mkdir -p dataset/
	python ./fetch.py works
	python ./fetch.py reviews
	python ./fetch.py records
	python ./fetch.py staffs

dataset-stat:
	bash dataset/stat.sh
