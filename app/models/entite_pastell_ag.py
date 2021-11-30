from app import db


class EntitePastellAG(db.Model):
    __tablename__ = 'entite_pastell_ag'
    id: int = db.Column(db.Integer, primary_key=True)
    siren: str = db.Column(db.String(9), nullable=False)
    id_e: str = db.Column(db.Integer, nullable=False)
    denomination: str = db.Column(db.String(256), nullable=True)

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id': self.id,
            'siren': self.siren,
            'id_e': self.id_e,
            'denomination': self.denomination
        }
