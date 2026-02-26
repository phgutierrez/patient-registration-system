/**
 * Apps Script Web App para agendamento automático no Google Calendar
 * 
 * DEPLOY:
 * 1. Abra https://script.google.com
 * 2. Novo projeto > Cole este código
 * 3. Implantação > Nova implantação
 * 4. Tipo: Aplicativo da Web
 * 5. Executar como: Eu (seu email)
 * 6. Quem tem acesso: Qualquer pessoa
 * 7. Copie a URL da implantação e configure em APPS_SCRIPT_SCHEDULER_URL
 */

/**
 * Processa requisições POST para criar eventos no Google Calendar
 */
function doPost(e) {
  try {
    // Parse JSON do corpo da requisição
    const requestData = JSON.parse(e.postData.contents);
    
    // Validar campos obrigatórios
    if (!requestData.calendarId) {
      return createResponse(false, 'calendarId é obrigatório');
    }
    if (!requestData.title) {
      return createResponse(false, 'title é obrigatório');
    }
    if (!requestData.date) {
      return createResponse(false, 'date é obrigatório (formato: YYYY-MM-DD)');
    }
    
    // Obter calendário
    let calendar;
    try {
      calendar = CalendarApp.getCalendarById(requestData.calendarId);
      if (!calendar) {
        return createResponse(false, `Calendário não encontrado: ${requestData.calendarId}`);
      }
    } catch (err) {
      return createResponse(false, `Erro ao acessar calendário: ${err.message}`);
    }
    
    // Parsear data (formato YYYY-MM-DD)
    const dateParts = requestData.date.split('-');
    if (dateParts.length !== 3) {
      return createResponse(false, 'Formato de data inválido. Use YYYY-MM-DD');
    }
    
    const year = parseInt(dateParts[0]);
    const month = parseInt(dateParts[1]) - 1; // Mês começa em 0
    const day = parseInt(dateParts[2]);
    const eventDate = new Date(year, month, day);
    
    // Montar descrição completa
    let description = requestData.description || '';
    
    // Adicionar informações adicionais na descrição se fornecidas
    let additionalInfo = [];
    
    if (requestData.orthopedist) {
      additionalInfo.push(`🩺 Ortopedista: ${requestData.orthopedist}`);
    }
    
    if (requestData.needs_icu) {
      additionalInfo.push(`🏥 Necessita vaga de UTI: Sim`);
    }
    
    if (requestData.opme && requestData.opme.length > 0) {
      additionalInfo.push(`🔧 OPME: ${requestData.opme.join(', ')}`);
    }
    
    if (requestData.opme_other) {
      additionalInfo.push(`🔧 OPME (outros): ${requestData.opme_other}`);
    }
    
    // Combinar descrição original com informações adicionais
    if (additionalInfo.length > 0) {
      description = description + '\n\n---\n' + additionalInfo.join('\n');
    }
    
    // Criar evento ALL-DAY
    const event = calendar.createAllDayEvent(
      requestData.title,
      eventDate,
      {
        description: description
      }
    );
    
    // Retornar sucesso com dados do evento
    return createResponse(true, 'Evento criado com sucesso', {
      eventId: event.getId(),
      htmlLink: event.getHtmlLink(),
      title: event.getTitle(),
      date: requestData.date
    });
    
  } catch (error) {
    Logger.log('Erro no doPost: ' + error.toString());
    return createResponse(false, `Erro ao processar requisição: ${error.toString()}`);
  }
}

/**
 * Testa o endpoint via GET (apenas para debug)
 */
function doGet(e) {
  return ContentService.createTextOutput(
    JSON.stringify({
      status: 'ok',
      message: 'Apps Script Web App para agendamento no Google Calendar está ativo',
      timestamp: new Date().toISOString(),
      usage: 'Envie POST com JSON: {calendarId, title, date, description, orthopedist, opme, needs_icu}'
    })
  ).setMimeType(ContentService.MimeType.JSON);
}

/**
 * Cria resposta JSON padronizada
 */
function createResponse(ok, message, data) {
  const response = {
    ok: ok,
    message: message
  };
  
  if (data) {
    Object.assign(response, data);
  }
  
  return ContentService.createTextOutput(JSON.stringify(response))
    .setMimeType(ContentService.MimeType.JSON);
}
