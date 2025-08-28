import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/infer/")
async def infer_picture(file: UploadFile = File(...)):
    # Check if file is provided
    if file is None:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    # Check if file has a content_type and is an image
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File is not an image.")
    contents = await file.read()
    temp_filename = f"temp_{file.filename}"
    with open(temp_filename, "wb") as f:
        f.write(contents)
    try:
        from model_interface import test_model
        test_model(temp_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
    result = {"message": "Inference completed", "filename": file.filename}
    return JSONResponse(content=result)