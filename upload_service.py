#lets ppl upload photo to be classified
import os
import fastapi
from fastapi import FastAPI, File, UploadFile


app =  FastAPI()

@app.post("/upload_image/")
async def upload_image(file: UploadFile = File(...)):