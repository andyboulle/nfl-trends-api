from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import games
from app.routers import trends
from app.routers import game_trends
from app.routers import weekly_trends
from app.routers import upcoming_games

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

api_v1 = FastAPI()

api_v1.include_router(games.router)
api_v1.include_router(trends.router)
api_v1.include_router(upcoming_games.router)
api_v1.include_router(weekly_trends.router)
api_v1.include_router(game_trends.router, prefix="/trends")

app.mount("/api/v1", api_v1)

@app.get('/')
def read_root():
    return {'message': 'Welcome to the NFL Trends API!'}