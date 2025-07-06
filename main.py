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
    Extracts and validates SVG content, repairing common issues.
    """
    import xml.etree.ElementTree as ET
    
    # Regex to find the entire SVG block, from <svg to </svg>
    match = re.search(r'<svg.*?/svg>', svg_content, re.DOTALL | re.IGNORECASE)
    
    if match:
        svg_block = match.group(0).strip()
    else:
        # If no complete SVG block found, try to repair
        svg_block = svg_content.strip()
    
    # Repair common issues
    svg_block = _repair_svg_issues(svg_block)
    
    # Validate XML structure
    try:
        ET.fromstring(svg_block)
        return svg_block
    except ET.ParseError as e:
        # Try one more repair attempt
        svg_block = _aggressive_svg_repair(svg_block)
        try:
            ET.fromstring(svg_block)
            return svg_block
        except ET.ParseError:
            return ""

def _repair_svg_issues(svg_content: str) -> str:
    """
    Repair common SVG issues that cause parsing errors.
    """
    # Remove incomplete tags at the end
    incomplete_patterns = [
        r'<path[^>]*$',  # Incomplete path tags
        r'<[a-zA-Z][^>]*$',  # Any incomplete tag
        r'<[^>]*\s[a-zA-Z-]+=["\'"][^"\']*$',  # Incomplete attributes
    ]
    
    for pattern in incomplete_patterns:
        if re.search(pattern, svg_content):
            svg_content = re.sub(pattern, '', svg_content)
            break
    
    # Ensure SVG has proper closing tag
    if not svg_content.endswith('</svg>'):
        svg_content += '</svg>'
    
    # Fix unmatched quotes
    single_quotes = svg_content.count("'")
    double_quotes = svg_content.count('"')
    
    if single_quotes % 2 != 0:
        # Remove last incomplete attribute with single quotes
        svg_content = re.sub(r"\s[a-zA-Z-]+='[^']*$", "", svg_content)
    
    if double_quotes % 2 != 0:
        # Remove last incomplete attribute with double quotes  
        svg_content = re.sub(r'\s[a-zA-Z-]+="[^"]*$', "", svg_content)
    
    return svg_content.strip()

def _aggressive_svg_repair(svg_content: str) -> str:
    """
    More aggressive repair attempts for severely malformed SVG.
    """
    # Start fresh - extract everything up to the last complete tag
    lines = svg_content.split('\n')
    clean_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip lines that look incomplete
        if (line.startswith('<') and not line.endswith('>') and 
            not line.endswith('/>') and not line.endswith('-->')):
            continue
            
        clean_lines.append(line)
    
    result = '\n'.join(clean_lines)
    
    # Ensure proper SVG wrapper
    if not result.startswith('<svg'):
        result = '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1000" viewBox="0 0 800 1000">\n' + result
    
    if not result.endswith('</svg>'):
        result += '\n</svg>'
    
    return result

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