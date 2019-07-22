import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    print("running import.py")
    with open('books.csv') as f:
        filereader = csv.reader(f)
        # skip first row
        next(filereader)
        for isbn, title, author, year in filereader:
            db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                        {"isbn": isbn, "title": title, "author": author, "year": int(year)})
            print(f"Added book isbn {isbn}, {title}, author : {author} - {year}")
            db.commit()

if __name__ == "__main__":
    main()