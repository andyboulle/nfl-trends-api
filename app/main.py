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
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "https://nfl-trends-ui.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(games.router, prefix='/api/v1')
app.include_router(trends.router, prefix='/api/v1')
app.include_router(upcoming_games.router, prefix='/api/v1')
app.include_router(weekly_trends.router, prefix='/api/v1')
app.include_router(game_trends.router, prefix="/api/v1/trends")

@app.get('/')
def read_root():
    return {'message': 'Welcome to the NFL Trends API!'}