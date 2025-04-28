from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
db = SQLAlchemy(app)


@app.route('/patient/<int:patient_id>/surgery_request', methods=['GET', 'POST'])
@login_required
def surgery_request(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    if request.method == 'POST':
        patient.procedimento_solicitado = request.form.get(
            'procedimento_solicitado')
        patient.cid_procedimento = request.form.get('cid_procedimento')
        patient.data_prevista_cirurgia = datetime.strptime(
            request.form.get('data_prevista_cirurgia'), '%Y-%m-%dT%H:%M')
        patient.observacoes = request.form.get('observacoes')

        db.session.commit()
        flash('Solicitação de cirurgia atualizada com sucesso!', 'success')
        return redirect(url_for('patient_details', patient_id=patient.id))

    return render_template('surgery_request.html', patient=patient)
