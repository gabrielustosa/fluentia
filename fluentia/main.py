from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from starlette.responses import JSONResponse

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


@app.exception_handler(ValidationError)
async def validation_error_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={'detail': jsonable_encoder(exc.errors())},
    )
