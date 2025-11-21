from whoosh.index import open_dir

# 1. Open the Index
ix = open_dir("whoosh_index") # Ensure this path matches your config

print(f"Total Documents: {ix.doc_count()}")

with ix.searcher() as searcher:
    
    # --- TEST 1: CHECK GENRES (KEYWORD) ---
    # Expectation: Whole phrases like b'science fiction'
    print("\n🔍 TERMS IN 'GENRES' (First 10):")
    print("-" * 30)
    for i, term in enumerate(searcher.lexicon("genres")):
        print(f"  {term.decode('utf-8')}") # Whoosh stores terms as bytes
        if i >= 100: break

    # --- TEST 2: CHECK DIRECTOR (TEXT) ---
    # Expectation: Single words like b'christopher', b'nolan'
    print("\n🔍 TERMS IN 'DIRECTOR' (First 10):")
    print("-" * 30)
    for i, term in enumerate(searcher.lexicon("director")):
        print(f"  {term.decode('utf-8')}")
        if i >= 100: break

    # --- TEST 3: CHECK SPECIFIC WORD ---
    # See if "nolan" exists in director
    word = "nolan"
    if word in searcher.lexicon("director"):
         print(f"\n✅ The word '{word}' is indexed in 'director'.")
    else:
         print(f"\n❌ The word '{word}' is NOT found in 'director'.")