import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import uuid
from manager import connect_manager
router_evas = APIRouter()

logging.basicConfig(level=logging.INFO)


@router_evas.websocket("/WEBService/ServiceServer2")
async def normal_asr_loader(
    websocket: WebSocket, model_name: str = None, client_id: str = None
):
    client_id = client_id if client_id is not None else "tempx-" + str(uuid.uuid4())
    await engine_whisper(websocket, model_name, client_id)
    
@router_evas.websocket("/WEBService/normal")
async def normal_asr_loader(
    websocket: WebSocket, model_name: str = None, client_id: str = None
):
    client_id = client_id if client_id is not None else "tempx-" + str(uuid.uuid4())
    await engine_normal(websocket, model_name, client_id)
    
@router_evas.websocket("/WEBService/whisper")
async def whisper_asr_loader(
    websocket: WebSocket, model_name: str = None, client_id: str = None
):
    client_id = client_id if client_id is not None else "tempx-" + str(uuid.uuid4())
    await engine_whisper(websocket, model_name, client_id)
    


async def engine_normal(websocket: WebSocket, model_name: str, client_id: str):
    await websocket.accept()
    logging.info("啟動一般收音")
    logging.info("初始化辨識模型")
    models = await connect_manager.connect(websocket, client_id, model_name)

    try:
        while True:
            datas = await websocket.receive_bytes()
            if datas == b"":
                break

            await asyncio.to_thread(models.add_to_buffer, datas)
            last_chunk = await models.asr_flow_normal(websocket)
            if last_chunk:
                break

        await websocket.close()
        await connect_manager.disconnect(client_id)
        logging.info(
            "NOW CONNECTING COUNT: {}".format(len(connect_manager.connection2model))
        )
    except WebSocketDisconnect:
        await connect_manager.disconnect(client_id)
        logging.info("CLIENT SIDE DISCONNECT")
        logging.info(
            "NOW CONNECTING COUNT: {}".format(len(connect_manager.connection2model))
        )

async def engine_whisper(websocket: WebSocket, model_name: str, client_id: str):
    await websocket.accept()
    logging.info("啟動一般收音")
    logging.info("初始化辨識模型")
    audio_data = b""  # 累積音訊資料
    
    while True:
        try:
            datas = await websocket.receive_bytes()
            print(f"收到音訊，長度: {len(datas)}")
            if datas == b"":  # 判斷音訊流是否結束
                break
            if len(datas) % 2 != 0:
                print(f"修正音訊數據長度: {len(datas)} 不是 int16 的倍數")
                datas = datas[:-1]  # 丟棄最後一個 byte
            audio_data += datas  # 累積音訊資料
        except WebSocketDisconnect:
            logging.info("Client disconnected abruptly.")
            break  # 讓 while 迴圈結束        
        
    full_text = "Welcome to Kenkone"
    logging.info(f"辨識結果: {full_text}, 長度: {len(audio_data)}")
    output = {}
    output["data"] = [{"text": full_text}]
    output = json.dumps(output, ensure_ascii=False)
    output = output.encode(encoding="utf-8")
    await websocket.send_bytes(output)  # 將辨識結果送回前端
    await websocket.close()
