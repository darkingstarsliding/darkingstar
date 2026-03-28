import os
import uvicorn

if __name__=='__main__':
    uvicorn.run(
            "router.api_router:app",
            workers=1,
            )
