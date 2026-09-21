# Implementation Notes for FastAPI Assignment

This assignment implements an asynchronous FastAPI app for generating images with Stability's Stable Diffusion.

Users submit structured image requirements through the `POST /images`endpoint. The prompt is then converted into a custom prompt, a unique image ID is created, and the image generation is started as a FastAPI background task. The generated image can be retrieved through `GET /image/{image_id}`.

For the implementation, the provided `ImageGenerator`is used.

## Features
The app includes the following functionality:
* FastAPI-based REST API
* Structured custom prompt input
* Input validation using Pydantic
* Asynchronous image generation using FastAPI `BackgroundTasks`
* Unique image IDs generated using UUIDs
* Image generation through the provided `ImageGenerator`
* Generated images stored as PNG
* Retrieval of generated images by image_id
* Status handling for processing, completed, failed, and unknown image requests
* Retrieval of previously generated images after an application reload
* The optional part (GPT-based profanity check) is currently commented out due to an invalid OPENAI API KEY at time of creation/testing.

## Project Structure
Relevant files are located in the `assignment` directory.

assignment/
├── app.py
├── gpt_service.py
├── profanity_prompt.txt
├── image_generator/
├── generated_images/
├── pyproject.toml
├── uv.lock
└── IMPLEMENTATION.md

## Running the Application

The app is run from the `assignment` directory with **uv run uvicorn app:app --reload**.
FastAPI automatically provides interactive API documentation under **/docs**.
All inputs can be tested there.

## API Endpoints

### `POST /images`
Creates a new image-generation request.
The endpoint accepts structured image requirements rather than a single unstructured prompt.

Example request:
{
    "subject": "a small robot making coffee",
    "setting": "a futuristic space station kitchen",
    "mood": "playful",
    "details": "transparent pipes, mechanical arms and steam"
}

These fields are converted into a single prompt before sending the request to the image-generator.

Example response:
{
    "image_id": "1f479b08-7c41-43d9-b2e4-5b6f53c52825",
    "status": "processing"
}

The image itself is generated in the background.

### `GET /image/{image_id}`
Retrieves the result of an image-generation request.

Example:
GET /image/1f479b08-7c41-43d9-b2e4-5b6f53c52825

Possible outcomes are:
* processing: The image is still being generated.
* ready: The generated PNG is returned.
* failed: Image generation failed and an error is returned.
* unknown Image ID: The API returns HTTP 404.

If the app has been restarted and the in-memory job information is lost, the endpoint checks if a PNG with the corresponding image_id exists in the generated_images/ directory. If it exists, the stored image is returned.

## Prompt System
The following fields are supported:
* subject: The main object, person, scene, or concept that should appear in the image.
* setting: The environment or location in which the subject should appear.
* mood: The atmosphere or emotional tone of the image.
* details: Additional visual elements that should be included.

## Error Handling
### Invalid Requests
Checked by Pydantic and FastAPI. If e.g. an request omits the subject-field, we get an HTTP 422 Validation Error.

### Unknown Image IDs
In case of an unknown image_id, the API returns HTTP status 404 with details: "Image ID not found".

### Image Generation Failure
If the background image generation throws an exception, the corresponding job is marked as `failed`. The error information is stored so that it can be returned through the image retrieval endpoint.#

## Limitations

Current image-generation states are stored in an in-memory dictionary.
This provides a simple way to track whether a job is:

* processing
* ready
* failed

However, this status information is lost whenever the application restarts.
Generated PNG files are stored in disk and therefore remain available.
To compensate for the loss of job information after a restart, the rerieval endpoint checks the generated_images/ directory if no in-memory job exists.