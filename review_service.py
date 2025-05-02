import grpc
from concurrent import futures
import os # For environment variables
import psycopg # Or import psycopg2
import review_pb2
import review_pb2_grpc
import book_pb2
import book_pb2_grpc

# Use a single DATABASE_URL environment variable
DATABASE_URL = os.getenv(DATABASE_URI)

class ReviewService(review_pb2_grpc.ReviewServiceServicer):
    def __init__(self):
        
        self.book_channel = grpc.insecure_channel('localhost:50051')
        self.book_stub = book_pb2_grpc.BookServiceStub(self.book_channel)

        
        if not DATABASE_URL:
             print("❌ DATABASE_URL environment variable not set.")
             self.conn = None
        else:
            try:
                
                self.conn = psycopg.connect(DATABASE_URL)
                print("✅ Successfully connected to PostgreSQL via DATABASE_URL")
            except psycopg.OperationalError as e:
                print(f"❌ Could not connect to database using DATABASE_URL: {e}")
                
                self.conn = None # Indicate connection failure

    def AddReview(self, request, context):
        if not self.conn:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Database connection not available.")
            return review_pb2.ReviewResponse(status="Database connection error")

        try:
            book_resp = self.book_stub.GetBook(book_pb2.GetBookRequest(book_id=request.book_id))
            if not book_resp.exists:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Livro não encontrado")
                return review_pb2.ReviewResponse(status="Livro não encontrado")
        except grpc.RpcError as e:
             context.set_code(e.code())
             context.set_details(f"Error checking book service: {e.details()}")
             return review_pb2.ReviewResponse(status="Error checking book service")

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO reviews (book_id, rating, comment) VALUES (%s, %s, %s)",
                    (request.book_id, request.rating, request.comment)
                )
            self.conn.commit() # Commit the transaction
            print(f"📝 Review added for book_id {request.book_id}")
            return review_pb2.ReviewResponse(status="Avaliação registrada")
        except (Exception, psycopg.DatabaseError) as error:
            print(f"❌ Database error on insert: {error}")
            self.conn.rollback() # Rollback on error
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Failed to add review due to database error.")
            return review_pb2.ReviewResponse(status="Database insert error")


    def GetReviews(self, request, context):
        if not self.conn:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Database connection not available.")
            return review_pb2.ReviewList()

        reviews_list = []
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT book_id, rating, comment FROM reviews WHERE book_id = %s ORDER BY created_at DESC",
                    (request.book_id,)
                )
                
                results = cur.fetchall()
                for row in results:
                    
                    review_proto = review_pb2.Review(
                        book_id=row[0],
                        rating=row[1],
                        comment=row[2] if row[2] is not None else "" 
                    )
                    reviews_list.append(review_proto)
            print(f"📚 Found {len(reviews_list)} reviews for book_id {request.book_id}")
            return review_pb2.ReviewList(reviews=reviews_list)
        except (Exception, psycopg.DatabaseError) as error:
            print(f"❌ Database error on select: {error}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Failed to retrieve reviews due to database error.")
            return review_pb2.ReviewList()
def serve():
    service = ReviewService() 
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    review_pb2_grpc.add_ReviewServiceServicer_to_server(service, server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print("Review Service rodando em localhost:50052")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("🛑 Shutting down server...")
        if service.conn:
            service.conn.close()
            print("🔒 Database connection closed.")
        server.stop(0)

if __name__ == '__main__':
    serve()
