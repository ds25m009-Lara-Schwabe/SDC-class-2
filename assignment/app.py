import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from image_generator import ImageGenerator
from pydantic import BaseModel, Field
from typing import Optional

# from gpt_service import GPTService

app = FastAPI()

class ImageRequest(BaseModel):
    subject: str = Field(min_length=3, max_length=300)
    setting: Optional[str] = Field(default=None, max_length=300)
    mood: Optional[str] = Field(default=None, max_length=200)
    details: Optional[str] = Field(default=None, max_length=500)

def build_prompt(request: ImageRequest) -> str:
    prompt_parts = [request.subject]
    if request.setting:
        prompt_parts.append(f"set in {request.setting}")

    if request.mood:
        prompt_parts.append(f"with a {request.mood} atmosphere")

    if request.details:
        prompt_parts.append(f"featuring {request.details}")
    
    return ", ".join(prompt_parts)

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

stability_api_key = os.getenv("STABILITY_API_KEY")
# openai_api_key = os.getenv("OPENAI_API_KEY")
# profanity_prompt_file = os.getenv("PROFANITY_PROMPT_FILE")

if not stability_api_key:
    raise RuntimeError("STABILITY_API_KEY is not set in the environment variables.")

# if not openai_api_key:
#     raise RuntimeError("OPENAI_API_KEY is not set in the environment variables.")

# if not profanity_prompt_file:
#     raise RuntimeError("PROFANITY_PROMPT_FILE is not set in the environment variables.")

# profanity_prompt_path = Path(profanity_prompt_file)
# if not profanity_prompt_path.exists():
#     raise RuntimeError(f"Profanity prompt file '{profanity_prompt_file}' does not exist.")

# profanity_prompt = profanity_prompt_path.read_text(encoding="utf-8")

image_generator = ImageGenerator(stability_api_key)

# gpt_service = GPTService(
#     openai_api_key=openai_api_key,
#     profanity_prompt=profanity_prompt
# )

IMAGE_DIR = Path(__file__).resolve().parent / "generated_images"
IMAGE_DIR.mkdir(exist_ok=True)

image_jobs = {}


# Function to be run as a background task.
# This is just a placeholder function for demonstration.
# In your application, this could be a function that generates an image.
def write_log(message: str):
    # Example of a time-consuming task: Writing a message to a file.
    # Replace this with the logic of your image generation task.
    with open("log.txt", "a") as file:
        file.write(f"{message}\n")

@app.get("/example")
async def example_endpoint(background_tasks: BackgroundTasks):
    # This endpoint demonstrates how to add a background task.
    # The `write_log` function will be executed after the response is sent.
    # Note: The task runs in the same process but does not block the response.
    background_tasks.add_task(write_log, "Example endpoint was visited")
    return {"message": "This is an example endpoint"}

# TODO: Define your POST /images endpoint for asynchronous image generation
# This endpoint should accept a custom prompt, process it asynchronously,
# and return an image ID for later retrieval.

@app.post("/images")
async def create_image(
    request: ImageRequest,
    background_tasks: BackgroundTasks
):
    prompt = build_prompt(request)

    # Profanity check is disabled because the API Key is not working for me.
    # if gpt_service.contains_profanity(prompt):
    #     raise HTTPException(
    #         status_code=400,
    #         detail="Prompt was rejected because it contains inappropriate content."
    #     )

    image_id = str(uuid.uuid4())

    image_jobs[image_id] = {
        "status": "processing",
        "path": None,
        "error": None
    }
    background_tasks.add_task(
        gen_image_task, image_id, prompt
    )
    return {
        "image_id": image_id,
        "status": "processing"
    }

# TODO: Implement the background task function for image generation
# This function will use the ImageGenerator service to generate images
# based on the provided custom prompt and save them.

def gen_image_task(image_id: str, prompt: str):
    try:
        image_binary = image_generator.generate_image(prompt)

        if image_binary is None:
            raise RuntimeError("Image generation returned no image.")

        image_path = IMAGE_DIR / f"{image_id}.png"

        with open(image_path, "wb") as file:
            file.write(image_binary)

        image_jobs[image_id]["status"] = "ready"
        image_jobs[image_id]["path"] = str(image_path)

    except Exception as exc:
        image_jobs[image_id]["status"] = "failed"
        image_jobs[image_id]["error"] = str(exc)

# TODO: Create an endpoint for retrieving generated images
# The endpoint should take an image ID and return the corresponding image
# if it's ready, or an appropriate status message otherwise.
# TODO: Implement error handling for various possible failure scenarios

@app.get("/image/{image_id}")
async def get_image(image_id: str):
    job = image_jobs.get(image_id)
    image_path = IMAGE_DIR / f"{image_id}.png"

    # If the in-memory job entry is gone after a reload,
    # but the image file still exists, return the file anyway.
    if job is None:
        if image_path.exists():
            return FileResponse(
                path=image_path,
                media_type="image/png",
                filename=f"{image_id}.png"
            )

        raise HTTPException(
            status_code=404,
            detail="Image ID not found."
        )

    if job["status"] == "processing":
        return {
            "image_id": image_id,
            "status": "processing"
        }

    if job["status"] == "failed":
        return {
            "image_id": image_id,
            "status": "failed",
            "error": job["error"]
        }

    if job["status"] == "ready":
        return FileResponse(
            path=job["path"],
            media_type="image/png",
            filename=f"{image_id}.png"
        )

    raise HTTPException(
        status_code=500,
        detail="Unknown job status."
    )


# OPTIONAL: Implement any necessary profanity checking or validation for the user prompts

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
