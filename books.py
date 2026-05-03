from fastapi import FastAPI,Body
app = FastAPI()

BOOKS=[
    {"id": 1, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald","Category":"Novel"},
    {"id": 2, "title": "To Kill a Mockingbird", "author": "Harper Lee","Category":"Novel"},
    {"id": 3, "title": "1984", "author": "George Orwell","Category":"Dystopian"},
    {"id": 4, "title": "Pride and Prejudice", "author": "Jane Austen","Category":"Romance"},
    {"id": 5, "title": "The Catcher in the Rye", "author": "J.D. Salinger","Category":"Novel"},
    
]

@app.get("/api-endpoint")
async def first_api():
    return BOOKS

@app.get("/api-endpoint/{dynamic_parameter}")
async def read_all_books(dynamic_parameter: str):
    return {"message": f"You requested books with the parameter: {dynamic_parameter}"}

@app.get("/books/")
async def read_category_books(category: str):
    category_books = [book for book in BOOKS if book["Category"].lower() == category.lower()]
    return {"books": category_books}

@app.get("/books/{book_author}")
async def read_author_books(book_author: str,category: str = None):
    author_books = [book for book in BOOKS if book["author"].lower() == book_author.lower()]
    if category:
        author_books = [book for book in author_books if book["Category"].lower() == category.lower()]
    return {"books": author_books}

@app.post("/books/create_book")
async def create_book(book=Body()):
    BOOKS.append(book)
    return {"message": "Book created successfully", "book": BOOKS[-1]}

@app.put("/books/update_book/{book_id}")
async def update_book(book_id: int, updated_book=Body()):
    for index, book in enumerate(BOOKS):
        if book["id"] == book_id:
            BOOKS[index] = updated_book
            return {"message": "Book updated successfully", "updated_book": updated_book, "books": BOOKS}
    return {"message": "Book not found"}

@app.delete("/books/delete_book/{book_id}")
async def delete_book(book_id: int):
    for index, book in enumerate(BOOKS):
        if book["id"] == book_id:
            deleted_book = BOOKS.pop(index)
            return {"message": "Book deleted successfully", "deleted_book": deleted_book, "books": BOOKS}
    return {"message": "Book not found"}