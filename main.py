import uvicorn

if __name__ == "__main__":
    config = uvicorn.Config(
        "src.api.server:app", port=3000, log_level="info", reload=True, env_file=".env", use_colors=True,
    )
    server = uvicorn.Server(config)
    server.run()
