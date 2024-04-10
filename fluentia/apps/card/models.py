from datetime import datetime

import sqlmodel as sm
from fastapi import HTTPException, status

from fluentia.apps.term.constants import Language
from fluentia.apps.term.models import Term
from fluentia.core.model.shortcut import create, update


class CardSet(sm.SQLModel, table=True):
    id: int = sm.Field(primary_key=True)
    name: str
    description: str | None = None
    created_at: datetime = sm.Field(
        sa_column=sm.Column(sm.DateTime(timezone=True), server_default=sm.func.now())
    )
    updated_at: datetime | None = sm.Field(
        sa_column=sm.Column(sm.DateTime(timezone=True), onupdate=sm.func.now())
    )

    language: str | None = None
    user_id: int = sm.Field(foreign_key='user.id')

    @staticmethod
    def create(session, **data):
        return create(CardSet, session, **data)

    @staticmethod
    def list(session, user_id, name=None):
        filters = set()
        if name:
            filters.add(
                sm.func.clean_text(CardSet.name).like(
                    '%' + sm.func.clean_text(name) + '%'
                )
            )
        return session.exec(
            sm.select(CardSet).where(
                CardSet.user_id == user_id,
                *filters,
            )
        )

    @staticmethod
    def update(session, db_cardset, **data):
        return update(session, db_cardset, **data)

    @staticmethod
    def delete(session, db_cardset):
        session.delete(db_cardset)
        session.commit()


class Card(sm.SQLModel, table=True):
    id: int = sm.Field(primary_key=True)
    cardset_id: int = sm.Field(foreign_key='cardset.id')
    created_at: datetime = sm.Field(
        sa_column=sm.Column(sm.DateTime(timezone=True), server_default=sm.func.now())
    )
    updated_at: datetime | None = sm.Field(
        sa_column=sm.Column(sm.DateTime(timezone=True), onupdate=sm.func.now())
    )
    note: str | None = None
    term: str
    origin_language: Language

    __table_args__ = (
        sm.ForeignKeyConstraint(
            ['term', 'origin_language'],
            ['term.term', 'term.origin_language'],
            ondelete='CASCADE',
        ),
    )

    @staticmethod
    def create(session, **data):
        db_term = Term.get_or_404(
            session,
            term=data['term'],
            origin_language=data['origin_language'],
        )
        data['term'] = db_term.term
        data['origin_language'] = db_term.origin_language

        return create(Card, session, **data)

    @staticmethod
    def list(session, cardset_id, term=None, note=None):
        filters = set()
        if term:
            filters.add(
                sm.func.clean_text(Card.term).like('%' + sm.func.clean_text(term) + '%')
            )
        if note:
            filters.add(
                sm.func.clean_text(Card.note).like(
                    '%' + sm.func.clean_text(note) + '%'
                ),
            )
        return session.exec(
            sm.select(Card).where(Card.cardset_id == cardset_id, *filters)
        )

    @staticmethod
    def get_or_404(session, id, user_id):
        db_card = session.exec(
            sm.select(Card)
            .join(CardSet, CardSet.id == Card.cardset_id)  # pyright: ignore[reportArgumentType]
            .where(Card.id == id, CardSet.user_id == user_id)
        ).first()
        if db_card is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Card object does not exists',
            )
        return db_card

    @staticmethod
    def update(session, db_card, **data):
        return update(session, db_card, **data)

    @staticmethod
    def delete(session, db_cardset):
        session.delete(db_cardset)
        session.commit()
