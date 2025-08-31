import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # Production configuration - no reload, proper timeout
    uvicorn.run(
        "core.api:app", 
        host="0.0.0.0", 
        port=port, 
        reload=False,  # Disable reload for production
        workers=1,     # Single worker for Cloud Run
        timeout_keep_alive=30,
        access_log=True
    )
