"""Pareamento e diagnóstico da sincronização offline-first."""
from __future__ import annotations

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from src.extensions import db
from src.models.sync import SyncAuditRevision
from src.runtime_security import request_is_loopback, require_admin
from src.sync.adapters import adapters_by_name, decode_value
from src.sync import sync_service
from src.sync.crypto import SyncCryptoError


sync_bp = Blueprint('sync', __name__, url_prefix='/sincronizacao')


def _complete_station_sync(runtime) -> None:
    """Conclui um pareamento já validado; pode ser repetido com segurança."""
    if runtime is None or not runtime.master_key:
        raise RuntimeError(
            'A chave ainda não está disponível nesta estação. Informe-a novamente.'
        )

    # Um erro anterior torna runtime.ready falso. Limpe-o somente durante esta
    # tentativa; qualquer nova falha volta a bloquear o uso e mantém o botão de
    # recuperação visível.
    runtime.error = None
    try:
        sync_service.restore_latest_checkpoint()
        sync_service.sync_once()
        sync_service.enqueue_baseline()
        sync_service.start()
        sync_service.wake()
        (runtime.local_root / 'recovery.confirmed').write_text(
            'paired\n', encoding='utf-8'
        )
    except Exception as exc:
        runtime.error = str(exc)[:500]
        raise


def _flash_sync_failure(runtime, exc: Exception) -> None:
    runtime.error = str(exc)[:500]
    current_app.logger.warning(
        'Falha ao concluir pareamento da estação: etapa=restauracao tipo=%s',
        type(exc).__name__,
    )
    flash(
        'A chave está salva, mas a sincronização não terminou. '
        'Verifique o acesso à pasta compartilhada e tente novamente.',
        'error',
    )


@sync_bp.route('/configurar', methods=['GET', 'POST'])
def setup():
    runtime = sync_service.runtime
    if runtime is None or not runtime.enabled:
        flash('A sincronização não está habilitada nesta instalação.', 'info')
        return redirect(url_for('auth.select_user'))
    if not request_is_loopback():
        return render_template(
            'error.html',
            title='Configuração local necessária',
            message='O pareamento só pode ser feito no próprio computador.',
        ), 403

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'pair':
            try:
                sync_service.pair(request.form.get('recovery_key') or '')
                runtime = sync_service.runtime
                _complete_station_sync(runtime)
                flash('Estação pareada. A sincronização foi iniciada.', 'success')
                return redirect(url_for('auth.select_user'))
            except SyncCryptoError as exc:
                flash(str(exc), 'error')
            except (OSError, RuntimeError) as exc:
                _flash_sync_failure(runtime, exc)
        elif action == 'retry_sync':
            try:
                _complete_station_sync(runtime)
                flash('Sincronização concluída. Esta estação está pronta.', 'success')
                return redirect(url_for('auth.select_user'))
            except (OSError, RuntimeError, SyncCryptoError) as exc:
                _flash_sync_failure(runtime, exc)
        elif action == 'reload_runtime':
            try:
                sync_service.stop()
                runtime = sync_service.configure(
                    current_app._get_current_object()
                )
                if runtime.ready:
                    _complete_station_sync(runtime)
                    flash(
                        'A pasta compartilhada voltou a responder e a '
                        'sincronização foi concluída.',
                        'success',
                    )
                    return redirect(url_for('auth.select_user'))
                if runtime.pairing_required:
                    flash('Informe novamente a chave de recuperação.', 'info')
                elif runtime.recovery_key_once:
                    flash('Confirme que a chave inicial foi guardada.', 'info')
                else:
                    raise RuntimeError(
                        runtime.error
                        or 'A pasta compartilhada continua indisponível.'
                    )
            except (OSError, RuntimeError, SyncCryptoError) as exc:
                runtime = sync_service.runtime or runtime
                _flash_sync_failure(runtime, exc)
        elif action == 'confirm_recovery' and runtime.recovery_key_once:
            if request.form.get('saved_recovery') != 'yes':
                flash('Confirme que a chave foi guardada em local seguro.', 'error')
            else:
                (runtime.local_root / 'recovery.confirmed').write_text(
                    'confirmed\n', encoding='utf-8'
                )
                runtime.recovery_key_once = None
                flash('Chave confirmada. A implantação está pronta.', 'success')
                return redirect(url_for('auth.select_user'))
        else:
            flash('Ação de sincronização inválida.', 'error')

    return render_template('sync/setup.html', runtime=runtime)

@sync_bp.get('/status')
@login_required
def status():
    return jsonify(sync_service.status())


@sync_bp.post('/agora')
@login_required
def sync_now():
    try:
        result = sync_service.sync_once()
        return jsonify({'ok': True, **result})
    except Exception as exc:
        current_app.logger.warning('Sincronização manual falhou: %s', exc)
        return jsonify({
            'ok': False,
            **sync_service.status(),
            'message': 'Não foi possível acessar a pasta compartilhada agora.',
        }), 503

@sync_bp.get('/historico')
@login_required
@require_admin
def history():
    revisions = SyncAuditRevision.query.order_by(
        SyncAuditRevision.created_at.desc(), SyncAuditRevision.id.desc()
    ).limit(250).all()
    return render_template('sync/history.html', revisions=revisions)


@sync_bp.post('/historico/<int:revision_id>/restaurar')
@login_required
@require_admin
def restore_revision(revision_id: int):
    revision = SyncAuditRevision.query.get_or_404(revision_id)
    adapter = adapters_by_name().get(revision.entity_type)
    if adapter is None:
        flash('O tipo dessa revisão não é mais suportado.', 'error')
        return redirect(url_for('sync.history'))
    obj = adapter.model.query.filter_by(sync_uuid=revision.entity_uuid).first()
    if obj is None:
        flash('O registro original não existe nesta estação.', 'error')
        return redirect(url_for('sync.history'))
    try:
        import json
        encoded_value = json.loads(revision.previous_value_json)
        if revision.field_name == '_deleted':
            obj.sync_deleted = bool(encoded_value)
        elif revision.field_name in adapter._reference_by_event:
            adapter.apply_reference(obj, revision.field_name, encoded_value)
        elif revision.field_name in adapter.fields:
            setattr(obj, revision.field_name, decode_value(encoded_value))
        else:
            raise ValueError('Campo não restaurável.')
        db.session.commit()
        sync_service.wake()
        flash('Versão restaurada e adicionada à fila de sincronização.', 'success')
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning('Falha ao restaurar revisão %s: %s', revision_id, exc)
        flash('Não foi possível restaurar esta versão.', 'error')
    return redirect(url_for('sync.history'))