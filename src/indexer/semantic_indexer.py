import faiss
import pickle

class SemanticIndexer:
    def __init__(self):
        self.faiss_index = None
        self.doc_map = None
        

    def preprocess_dataframe(self, dataframe, cols_to_combine=None):
        """
        Combine specified columns into a formatted combined_text column.
        If cols_to_combine is None, defaults to ['title', 'overview', 'genres', 'director']
        """
        if cols_to_combine is None:
            cols_to_combine = ['title', 'overview', 'genres', 'director', 'actors','characters']
        
        # Fill NaN values with empty strings
        dataframe = dataframe.fillna('')
        
        # Create combined_text for each row
        def combine_row(row):
            parts = []
            for col in cols_to_combine:
                if col in dataframe.columns and row[col]:
                    parts.append(f"{col.capitalize()}: {row[col]}")
            return "\n".join(parts)
        
        dataframe['combined_text'] = dataframe.apply(combine_row, axis=1)
        return dataframe
        
    
    def index(self, dataframe, embedder, cols_to_combine=None):
        """Build FAISS index from dataframe"""
        # Preprocess if combined_text doesn't exist
        if 'combined_text' not in dataframe.columns:
            dataframe = self.preprocess_dataframe(dataframe, cols_to_combine)
        
        vectors = []
        doc_map = {}
        
        for idx, row in dataframe.iterrows():
            # Use combined_text if available, otherwise fallback to simple concatenation
            if 'combined_text' in dataframe.columns and row['combined_text']:
                text = row['combined_text']
            else:
                text = f"{row.get('title', '')} {row.get('overview', '')} {row.get('genres', '')}"
            vectors.append(text)
            doc_map[idx] = {
                "id": str(row['id']),
                "title": row['title'],
                "year": int(row['year']) if str(row['year']).isdigit() else 0,
                "genres": str(row['genres']).lower(),
                "rating": float(row['rating']) if str(row['rating']).replace('.','').isdigit() else 0.0
            }
        
        embeddings = embedder.encode(vectors, show_progress_bar=True)
        dimension = embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)
        faiss.normalize_L2(embeddings)
        self.faiss_index.add(embeddings)
        self.doc_map = doc_map
    
    def search(self, query_text, embedder, filters=None, k=100):
        """Search with post-filtering"""
        vec = embedder.encode([query_text])
        faiss.normalize_L2(vec)
        D, I = self.faiss_index.search(vec, k=k)
        
        results = {}
        for rank, idx in enumerate(I[0]):
            if idx == -1:
                continue
            
            doc_id = self.doc_map[idx]['id']
            meta = self.doc_map[idx]
            
            # Apply filters
            if filters:
                if filters.get('year_min') and not (filters['year_min'] <= meta['year'] <= filters.get('year_max', 9999)):
                    continue
                if filters.get('genre') and filters['genre'].lower() not in meta['genres']:
                    continue
            
            results[doc_id] = D[0][rank]
        
        return results
    
    def save(self, index_path, doc_map_path):
        """Save index and doc_map to disk"""
        faiss.write_index(self.faiss_index, index_path)
        with open(doc_map_path, 'wb') as f:
            pickle.dump(self.doc_map, f)
    
    def load(self, index_path, doc_map_path):
        """Load index and doc_map from disk"""
        self.faiss_index = faiss.read_index(index_path)
        with open(doc_map_path, 'rb') as f:
            self.doc_map = pickle.load(f)


if __name__ == "__main__":
    import pandas as pd
    import sys
    import os
    
    # Add parent directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from config.loader import load_config
    from sentence_transformers import SentenceTransformer
    
    def preprocess_dataframe(df):
        df['combined_text'] = (
            df['title'].fillna('') + " " + df['overview'].fillna('')
        ).str.strip()
        df.fillna('', inplace=True)
        return df

    df = pd.read_csv('../msrd/dataset/movies.csv', sep='\t')
    df = preprocess_dataframe(df)
    # print(df.head())

    config = load_config()
    embedder = SentenceTransformer(config['embedding']['model'])
    
    indexer = SemanticIndexer()

    # indexer.index(df, embedder,cols_to_combine=["title", "overview", "genres"])
    # indexer.save(config['indexer']['semantic']['index_path'], config['indexer']['semantic']['doc_map_path'])
    indexer.load(config['indexer']['semantic']['index_path'], config['indexer']['semantic']['doc_map_path'])
    
    query_text = "Best Movies starring a Muslim character, about 9/11"
    index_dict = indexer.search(query_text, embedder, filters=None, k=100)
    count = 0
    cols_to_display = ["title", "overview", "genres", "year", "rating", "director","actors","characters"]

    for index, score in index_dict.items():
        index = int(index)
        print(index,score)
        
        for col in cols_to_display:
            print(f"{col}: {df.loc[df['id'] == index, col].values}")
        print("--------------------------------")

        if count == 5:
            break
        
        count += 1