from fastapi import FastAPI

from fluentia.apps.card.api import card_router
from fluentia.apps.exercises.api import exercise_router
from fluentia.apps.term.api import term_router
from fluentia.apps.user.api import user_router
from fluentia.apps.user.auth.api import auth_router

app = FastAPI()

app.include_router(term_router)
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(card_router)
app.include_router(exercise_router)
