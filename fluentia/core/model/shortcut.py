from fastapi import HTTPException, status
from sqlmodel import select


def get_object_or_404(Model, session, **kwargs):
    obj = session.exec(select(Model).filter_by(**kwargs)).first()
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'{Model.__name__} object does not exists.',
        )
    return obj


def get_or_create_object(Model, session, defaults=None, **kwargs):
    instance = session.exec(select(Model).filter_by(**kwargs)).first()
    if instance:
        return instance, False
    else:
        try:
            kwargs |= defaults or {}
            instance = Model(**kwargs)
            session.add(instance)
            session.commit()
        except Exception:
            session.rollback()
            instance = session.exec(select(Model).filter_by(**kwargs).one())
            return instance, False
        else:
            return instance, True
