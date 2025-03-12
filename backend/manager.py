from typing import Dict
from fastapi import WebSocket
from pathlib import Path
import datetime
import wave
import os
import struct

import uuid
import logging

logging.basicConfig(level=logging.INFO)

import json
import gc

import asyncio
import time


class Models:
    def __init__(self, websocket, model_name, client_id):
        self.chunk_size = 4096  #  self.chunk_size / 2 (2bits) / 16000 = 實際秒數
        self.array_queue_size = 16
        self.total_bytes = []
        self.buffer_bytes = b""

        ## kws 處理邏輯參數
        self.prev_can_do_asr = False
        self.can_do_asr = False
        self.start_idx = -1
        self.end_idx = -1
        self.consecutive_hit = 3
        self.keyword2ConsecutiveHit = {
            "hey_evas": 0,
            "hi_evas": 0,
            "evas_stop": 0,
            "evas_over": 0,
            "evas_go": 0,
            "finish": 0,
        }
        self.trigger_start_word = None
        self.trigger_end_word = None

    def get_models(self):
        return self.asr_model, self.kws_model, self.recorder

    def add_to_buffer(self, datas):
        self.buffer_bytes += datas

    def store_bytes(self, data):
        self.total_bytes.append(data)
        return True

    async def asr_flow_normal(self, websocket):
        flag = await asyncio.to_thread(self.store_bytes, self.buffer_bytes)
        last_chunk = True
        output = {}
        output["data"] = [{"text": "test"}]
        logging.info("final result : {}".format(output["data"]))
        output = json.dumps(output, ensure_ascii=False)
        output = output.encode(encoding="utf-8")
        await websocket.send_bytes(output)

        return last_chunk

class ConnectionManager:
    def __init__(self):
        self.connection2model: Dict[str] = {}

    async def connect(self, websocket: WebSocket, client_id: str, model_name: str):

        logging.info("model_name: {}".format(model_name))
        logging.info("client_id: {}".format(client_id))

        if client_id not in self.connection2model:
            self.connection2model[client_id] = {}
            models = await asyncio.to_thread(Models, websocket, model_name, client_id)
        else:
            logging.error("already init model, use it")

        return models

    async def disconnect(self, client_id: str):
        logging.info("DISCONNECT ID : {}".format(client_id))

        self.connection2model[client_id] = None
        del self.connection2model[client_id]
        gc.collect()
        logging.info("NOW CONNECTING COUNT: {}".format(len(self.connection2model)))


connect_manager = ConnectionManager()
