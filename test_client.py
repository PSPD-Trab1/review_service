import os
import grpc
import review_pb2
import review_pb2_grpc

APP_PORT = os.getenv("APP_PORT")

def enviar_avaliacao(stub):
    review_request = review_pb2.AddReviewRequest(
        book_id=8,
        rating=5,
        comment="Excelente leitura!"
    )

    try:
        response = stub.AddReview(review_request)
        print("✅ Avaliação enviada:", response.status)
    except grpc.RpcError as e:
        print(f"❌ Erro ao enviar avaliação: {e.details()} (código: {e.code()})")

def listar_avaliacoes(stub, book_id):
    query = review_pb2.GetReviewsRequest(book_id=book_id)
    try:
        response = stub.GetReviews(query)
        print(f"\n📚 Avaliações do livro {book_id}:")
        if response.reviews:
            for r in response.reviews:
                print(f" - ID Livro: {r.book_id}, Nota: {r.rating}, Comentário: {r.comment}")
        else:
            print("Nenhuma avaliação encontrada.")
    except grpc.RpcError as e:
        print(f"❌ Erro ao consultar avaliações: {e.details()} (código: {e.code()})")

def run():
    channel = grpc.insecure_channel(f'localhost:{APP_PORT}')
    stub = review_pb2_grpc.ReviewServiceStub(channel)

    enviar_avaliacao(stub)
    listar_avaliacoes(stub, book_id=8)

if __name__ == '__main__':
    run()
