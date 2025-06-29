from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import cairosvg
import io
from PIL import Image
import base64
import os

app = FastAPI(title="SVG to PNG Converter", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tools.a-g-e-n-t.de"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SVGRequest(BaseModel):
    svg_content: str
    width: int = 800
    height: int = 600

@app.post("/convert")
async def convert_svg_to_png(request: SVGRequest):
    try:
        png_bytes = cairosvg.svg2png(
            bytestring=request.svg_content.encode('utf-8'),
            output_width=request.width,
            output_height=request.height
        )
        
        png_base64 = base64.b64encode(png_bytes).decode('utf-8')
        
        return {
            "png_data": png_base64,
            "width": request.width,
            "height": request.height
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error converting SVG: {str(e)}")

@app.get("/")
async def root():
    return {"message": "SVG to PNG Converter API"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)