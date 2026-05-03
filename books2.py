from http.client import HTTPException,status
from typing import Optional

from fastapi import FastAPI, Body, Path,Query
from pydantic import BaseModel, Field


app = FastAPI()

class Book:
    id: int
    title: str
    author: str
    description: str
    rating: int
    published_date: Optional[int] = None
    def __init__(self, id: int, title: str, author: str, description: str, rating: int, published_date: Optional[int] = None):
        self.id = id
        self.title = title
        self.author = author
        self.description = description
        self.rating = rating
        self.published_date = published_date

class BookRequest(BaseModel):
    id: Optional[int] = Field(None, description="The ID of the book, it will be generated automatically if not provided")   
    title: str = Field(min_length=3)
    author: str=Field(min_length=1)
    description: str=Field(min_length=1,max_length=100)
    rating: int=Field(gt=0, lt=6)
    published_date: Optional[int] = Field(None, description="The published date of the book in YYYY-MM-DD format")
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "A new book",
                 "author": "codingwithsring",
                 "description": "This is a new book",
                 "rating": 5,
                 "published_date": 2024
            }
        }
    }
    
        
BOOKS=[Book(1, "Book 1", "Author 1", "Description 1", 5, 2023),
       Book(2, "Book 2", "Author 2", "Description 2", 4, 2024),
       Book(3, "Book 3", "Author 3", "Description 3", 3, 2025),
       Book(4, "Book 4", "Author 4", "Description 4", 2, 2026),
       Book(5, "Book 5", "Author 5", "Description 5", 1, 2023),
       Book(6, "Book 6", "Author 6", "Description 6", 5, 2024),
       Book(7, "Book 7", "Author 7", "Description 7", 4, 2025),
       Book(8, "Book 8", "Author 8", "Description 8", 3, 2026)]

@app.get("/books/{book_id}",status_code=status.HTTP_200_OK)
async def read_book(book_id: int):
    for book in BOOKS:
        if book.id == book_id:
            return {"id": book.id, "title": book.title, "author": book.author, "description": book.description, "rating": book.rating}
    raise HTTPException(status_code=404, detail="Book not found")

@app.get("/books/{rating}",status_code=status.HTTP_200_OK)
def read_books(rating: Optional[int] = None):
    """List all books, or pass ?rating=4 to filter by rating."""
    books_list = []
    for book in BOOKS:
        if rating is not None and book.rating != rating:
            continue
        if rating is not None:
            books_list.append(
                {"id": book.id, "title": book.title, "author": book.author, "description": book.description, "rating": book.rating}
            )
        else:
            books_list.append(
                {book.id: {"title": book.title, "author": book.author, "description": book.description, "rating": book.rating}}
            )
    return books_list

@app.post("/books/create_book",status_code=status.HTTP_201_CREATED)
async def create_book(book: BookRequest):
    new_book = Book(**book.dict())
    BOOKS.append(find_book_id(new_book))
    return {"message": "Book created successfully", "book": {"id": new_book.id, "title": new_book.title, "author": new_book.author, "description": new_book.description, "rating": new_book.rating}}

def find_book_id(book:Book):
    if len(BOOKS)>0:
        book.id=BOOKS[-1].id+1
    else:
        book.id=1
    return book

@app.put("/books/update_book/{book_id}",status_code=status.HTTP_204_NO_CONTENT)
async def update_book(book_id: int, book: BookRequest):
    for idx, existing_book in enumerate(BOOKS):
        if existing_book.id == book_id:
            updated_book = Book(**book.dict())
            updated_book.id = book_id
            BOOKS[idx] = updated_book
            return {"message": "Book updated successfully", "book": {"id": updated_book.id, "title": updated_book.title, "author": updated_book.author, "description": updated_book.description, "rating": updated_book.rating}}
    raise HTTPException(status_code=404, detail="Book not found")

@app.delete("/books/delete_book/{book_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int=Path(description="The ID of the book to delete",gt=0)):
    for idx, existing_book in enumerate(BOOKS):
        if existing_book.id == book_id:
            del BOOKS[idx]
            return {"message": "Book deleted successfully"}
    raise HTTPException(status_code=404, detail="Book not found")

@app.get("/books/published_date/{published_date}",status_code=status.HTTP_200_OK)
async def read_books_by_published_date(published_date: int):
    books_list = []
    print(published_date,'published_date')
    for book in BOOKS:
        if book.published_date == published_date:
            books_list.append(
                {"id": book.id, "title": book.title, "author": book.author, "description": book.description, "rating": book.rating, "published_date": book.published_date}
            )
    return books_list
