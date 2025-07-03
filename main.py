from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import cairosvg
import io
from PIL import Image
import base64
import os
import re

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

def _clean_svg_content(svg_content: str) -> str:
    """
    Extracts the core SVG content from a potentially noisy string using regex.
    It looks for the first <svg> tag and the last </svg> tag, ignoring case and surrounding text.
    """
    # Regex to find the entire SVG block, from <svg to </svg>
    # re.DOTALL allows . to match newlines, re.IGNORECASE makes it case-insensitive
    match = re.search(r'<svg.*?/svg>', svg_content, re.DOTALL | re.IGNORECASE)
    
    if match:
        # Return the matched SVG block, stripped of any leading/trailing whitespace
        return match.group(0).strip()
    else:
        # If no <svg>...</svg> block is found, the input is considered invalid.
        return ""

@app.post("/convert")
async def convert_svg_to_png(request: SVGRequest):
    try:
        cleaned_svg = _clean_svg_content(request.svg_content)
        
        if not cleaned_svg:
            raise HTTPException(status_code=400, detail="Could not find a valid <svg>...</svg> block in the input.")

        png_bytes = cairosvg.svg2png(
            bytestring=cleaned_svg.encode('utf-8'),
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
        # Catching specific cairosvg errors could be more granular, but this is a safe fallback.
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