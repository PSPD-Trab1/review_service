VENV=venv

PROTO_FILES=bookstore.proto review.proto

init:
	uv sync

protos:
	@for file in $(PROTO_FILES); do \
		uv run python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. $$file; \
	done

start:
	uv run --env-file .env review_service.py

clean:
	rm -rf $(VENV) __pycache__ *.pyc *_pb2.py *_pb2_grpc.py

test:
	uv run --env-file .env test_client.py