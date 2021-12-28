import sqlalchemy as _db

from . import orm as _orm



class ChatLog(_orm.ModelBase):
    ID_COLUMN_NAME: str = 'chat_log_id'
    TABLE_NAME: str = 'chat_log'
    __tablename__ = TABLE_NAME

    id = _db.Column(ID_COLUMN_NAME, _db.Integer, primary_key=True, autoincrement=True, nullable=False)
    guild_id = _db.Column('guild_id', _db.Integer, nullable=False)
    channel_id = _db.Column('channel_id', _db.Integer, nullable=False)
    pss_channel_key = _db.Column('pss_channel_key', _db.Text, nullable=False)
    is_active = _db.Column('is_active', _db.Boolean, nullable=False, default=False)
    last_pss_message_id = _db.Column('last_pss_message_id', _db.Integer, nullable=False)
    name = _db.Column('name', _db.Text, nullable=False)


    def __repr__(self) -> str:
        return f'<ChatLog id={self.id} name={self.name}>'


    def __str__(self) -> str:
        return f'\'{self.name}\' (ID: {self.id})'


    @classmethod
    def make(cls,
             guild_id: int,
             message_channel_id: int,
             pss_channel_key: str,
             name: str
    ) -> 'ChatLog':
        result = ChatLog(
            guild_id=guild_id,
            channel_id=message_channel_id,
            pss_channel_key=pss_channel_key,
            name=name,
            )
        return result