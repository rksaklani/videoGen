"""Template gallery — pre-made avatars users can pick from."""
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from loguru import logger

router = APIRouter(prefix="/templates", tags=["Templates"])

# Template definitions — add more by dropping images in Backend/assets/templates/
TEMPLATES = [
    {
        "id": "business-man",
        "name": "Business Man",
        "category": "professional",
        "description": "Professional male in a suit, studio background",
        "image": "templates/business_man.png",
        "suggested_prompt": "A professional man speaking in a modern office",
        "suggested_voice": "en-male",
    },
    {
        "id": "business-woman",
        "name": "Business Woman",
        "category": "professional",
        "description": "Professional female in business attire, studio background",
        "image": "templates/business_woman.png",
        "suggested_prompt": "A professional woman presenting in a conference room",
        "suggested_voice": "en-female",
    },
    {
        "id": "casual-male",
        "name": "Casual Male",
        "category": "casual",
        "description": "Casual young man, outdoor setting",
        "image": "templates/casual_male.png",
        "suggested_prompt": "A young man talking casually outdoors",
        "suggested_voice": "en-male",
    },
    {
        "id": "casual-female",
        "name": "Casual Female",
        "category": "casual",
        "description": "Casual young woman, bright background",
        "image": "templates/casual_female.png",
        "suggested_prompt": "A young woman speaking in a bright room",
        "suggested_voice": "en-female",
    },
    {
        "id": "cartoon-character",
        "name": "Cartoon Character",
        "category": "creative",
        "description": "Animated cartoon style character",
        "image": "templates/cartoon.png",
        "suggested_prompt": "An animated character speaking enthusiastically",
        "suggested_voice": "en-male",
    },
]

# Also include the sample images that come with the model
SAMPLE_TEMPLATES = []
ASSETS_DIR = Path("Backend/assets/image")
if ASSETS_DIR.exists():
    for img in sorted(ASSETS_DIR.glob("*.png")):
        SAMPLE_TEMPLATES.append({
            "id": f"sample-{img.stem}",
            "name": f"Sample {img.stem}",
            "category": "samples",
            "description": f"Built-in sample image {img.stem}",
            "image": str(img),
            "suggested_prompt": "A person speaking naturally",
            "suggested_voice": "en-male",
        })


@router.get("/list")
async def list_templates(category: str = None):
    """List all available avatar templates."""
    all_templates = TEMPLATES + SAMPLE_TEMPLATES

    if category:
        all_templates = [t for t in all_templates if t["category"] == category]

    # Check which templates have actual image files
    available = []
    for t in all_templates:
        t["available"] = os.path.exists(t["image"])
        available.append(t)

    categories = list(set(t["category"] for t in TEMPLATES + SAMPLE_TEMPLATES))

    return {
        "templates": available,
        "categories": categories,
        "total": len(available),
    }


@router.get("/{template_id}")
async def get_template(template_id: str):
    """Get a specific template by ID."""
    all_templates = TEMPLATES + SAMPLE_TEMPLATES
    template = next((t for t in all_templates if t["id"] == template_id), None)
    if not template:
        raise HTTPException(404, f"Template not found: {template_id}")
    return template


@router.get("/{template_id}/image")
async def get_template_image(template_id: str):
    """Download a template's reference image."""
    all_templates = TEMPLATES + SAMPLE_TEMPLATES
    template = next((t for t in all_templates if t["id"] == template_id), None)
    if not template:
        raise HTTPException(404, f"Template not found: {template_id}")
    if not os.path.exists(template["image"]):
        raise HTTPException(404, f"Template image not found on disk")

    return FileResponse(template["image"], media_type="image/png")
