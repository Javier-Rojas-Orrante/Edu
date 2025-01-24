from Language.pdf_reader_service import PDFReaderService

path = 'books/Francais-inclusif-An-Interactive-Textbook-for-French-101-1717708299.pdf'

# Step 1: Display and get the Table of Contents with keys
toc = PDFReaderService.get_table_of_contents(path)

# Step 2: Retrieve the contents of a specific chapter using its key
chapter_key = 8  # Replace with the key from the TOC
chapter_contents = PDFReaderService.get_chapter_contents(path, chapter_key)

if chapter_contents:
    print(f"\nContents of Chapter {chapter_key}:\n")
    print(chapter_contents[:1000])  # Print the first 1000 characters of the chapter