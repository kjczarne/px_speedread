CREATE TABLE IF NOT EXISTS main(
    id INT NOT NULL PRIMARY KEY,
    date DATE,
    wpm INT,
    book_id TEXT,
    FOREIGN KEY (book_id) REFERENCES books(id)
);
CREATE TABLE IF NOT EXISTS books(
    id INT NOT NULL PRIMARY KEY,
    name TEXT,
    author TEXT,
    thresh_lines INT,
    thresh_pages INT,
    wpp INT,
    wpl INT
);
