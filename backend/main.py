from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 載入 WebSocket 路由
from evap_api import router_evas  # 替換成你的實際路由檔案名稱

app = FastAPI()

# 設定 CORS（如果你的前端需要跨域請求）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許所有來源
    allow_credentials=True,
    allow_methods=["*"],  # 允許所有 HTTP 方法
    allow_headers=["*"],  # 允許所有 Header
)

# 註冊 WebSocket 路由
app.include_router(router_evas)

@app.get("/")
async def root():
    return {"message": "WebSocket Server is Running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
