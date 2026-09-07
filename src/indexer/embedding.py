import numpy as np
from typing import List

class EmbeddingEngine:
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"):
        # Import lazily so the module can be imported without installing sentence-transformers if not used
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("Please install sentence-transformers to use EmbeddingEngine")

        self.model_name = model_name
        self.model = SentenceTransformer(model_name, local_files_only=True)
        
        # mpnet-base-v2 defaults to 128 in sentence_bert_config.json for speed, 
        # but the underlying transformer supports 512. We override it to 512 
        # to avoid silent truncation of our M2 chunks (which can reach ~264 tokens).
        if "mpnet-base-v2" in model_name:
            self.model.max_seq_length = 512
            
        self.max_seq_length = self.model.max_seq_length
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        # Extract huggingface commit hash if available
        self.revision = "main"
        try:
            for module in self.model._modules.values():
                if hasattr(module, "auto_model") and hasattr(module.auto_model, "config"):
                    self.revision = getattr(module.auto_model.config, "_commit_hash", "main")
                    break
        except Exception:
            pass
        
    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Encode a list of texts into dense vectors.
        Fails fast if any text exceeds max_seq_length.
        L2 normalizes the embeddings.
        """
        for text in texts:
            # Check exact token length including special tokens
            tokens = self.model.tokenizer.encode(text)
            if len(tokens) > self.max_seq_length:
                raise ValueError(f"Chunk exceeds max_seq_length ({len(tokens)} > {self.max_seq_length}). Truncation is disabled.")
                
        # encode with normalize_embeddings=True applies L2 norm automatically
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings
