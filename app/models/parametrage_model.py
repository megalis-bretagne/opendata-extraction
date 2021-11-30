from app import db

class Parametrage(db.Model):
    __tablename__ = 'parametrage'
    id: int = db.Column(db.Integer, primary_key=True)
    siren: str = db.Column(db.String(9), nullable=False)
    open_data_active = db.Column('open_data_active', db.Boolean(), nullable=False, server_default='0')
    publication_data_gouv_active = db.Column('publication_data_gouv_active', db.Boolean(), nullable=False, server_default='0')
    uid_data_gouv: str = db.Column(db.String(256), nullable=True)
    api_key_data_gouv: str = db.Column(db.String(256), nullable=True)
    created_at: str = db.Column(db.DateTime(), nullable=False)
    modified_at: str = db.Column(db.DateTime(), nullable=False)

    @property
    def serialize(self):
       """Return object data in easily serializable format"""
       return {
           'id'         : self.id,
           'siren': self.siren,
           'open_data_active': self.open_data_active,
           'publication_data_gouv_active': self.publication_data_gouv_active,
           'uid_data_gouv': self.uid_data_gouv,
           'api_key_data_gouv': self.api_key_data_gouv
       }
    @property
    def serialize_many2many(self):
       """
       Return object's relations in easily serializable format.
       NB! Calls many2many's serialize property.
       """
       return [ item.serialize for item in self.many2many]
