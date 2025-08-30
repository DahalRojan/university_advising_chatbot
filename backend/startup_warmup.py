#!/usr/bin/env python3
"""
Model warmup script for faster cold starts
Pre-loads models before serving requests
"""
import os
import sys
import time

def warmup_models():
    """Pre-load all models to avoid cold start delays"""
    print("🔥 Starting model warmup...")
    start_time = time.time()
    
    try:
        # Import and initialize retriever (loads BGE models)
        print("📦 Loading sentence transformers...")
        from core.retriever import bi_encoder, cross_encoder
        print(f"✅ BGE model loaded: {type(bi_encoder).__name__}")
        if cross_encoder:
            print(f"✅ Cross-encoder loaded: {type(cross_encoder).__name__}")
        else:
            print("⚠️ Cross-encoder not available")
            
        # Test encoding to ensure models are fully loaded
        test_text = "This is a test sentence for model warmup."
        embedding = bi_encoder.encode([test_text])
        print(f"✅ Model test successful, embedding shape: {embedding.shape}")
        
        # Initialize conversation intelligence components
        print("🧠 Loading conversation intelligence...")
        from features.intelligence.context_manager import ConversationContextManager
        from features.intelligence.query_consistency import QueryConsistencyEngine
        from features.intelligence.fallback_manager import SmartFallbackManager
        
        # Create instances to pre-load any dependencies
        context_manager = ConversationContextManager()
        consistency_engine = QueryConsistencyEngine()
        fallback_manager = SmartFallbackManager()
        print("✅ Conversation intelligence components loaded")
        
        elapsed = time.time() - start_time
        print(f"🎉 Model warmup completed in {elapsed:.2f} seconds")
        return True
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Model warmup failed after {elapsed:.2f} seconds: {e}")
        return False

if __name__ == "__main__":
    success = warmup_models()
    sys.exit(0 if success else 1)