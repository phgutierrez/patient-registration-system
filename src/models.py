class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    rg = db.Column(db.String(20), unique=True)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(8))
    procedimento_solicitado = db.Column(db.String(200))
    cid_procedimento = db.Column(db.String(10))
    data_prevista_cirurgia = db.Column(db.DateTime)
    observacoes = db.Column(db.Text)

    def __repr__(self):
        return f'<Patient {self.name}>'

