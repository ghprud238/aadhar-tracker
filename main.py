"""
Convenience entry point for local development.
Runs the FastAPI application on http://0.0.0.0:8000.
"""
import uvicorn


def main():
    uvicorn.run("services.api.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
