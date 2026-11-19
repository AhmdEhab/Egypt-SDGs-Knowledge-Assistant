import os
import sys
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"============================================================")
    print(f"  Egypt SDGs Knowledge Assistant | مساعد المعرفة لأهداف التنمية المستدامة")
    print(f"  Official MPED SDG Localization Knowledge Chatbot")
    print(f"  55 Reports | 1,053 Pages | 1,037 Chunks | 27 Governorates")
    print(f"  Server URL: http://localhost:{port}")
    print(f"============================================================")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)
