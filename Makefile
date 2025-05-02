VENV=venv

PROTO_FILES=book.proto review.proto

init:
	python -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install grpcio grpcio-tools
	$(VENV)/bin/pip install "psycopg[binary]"

protos:
	@for file in $(PROTO_FILES); do \
		$(VENV)/bin/python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. $$file; \
	done

run-book:
	$(VENV)/bin/python book_service.py

run-review:
	$(VENV)/bin/python review_service.py

clean:
	rm -rf $(VENV) __pycache__ *.pyc *_pb2.py *_pb2_grpc.py
