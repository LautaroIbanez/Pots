let summariesData = [];

async function loadSummaries() {
    try {
        const response = await fetch('/summaries');
        const data = await response.json();
        summariesData = data;
        renderSummaries();
    } catch (error) {
        console.error('Error loading summaries:', error);
        document.getElementById('content').innerHTML = '<div class="empty-state"><p>Error al cargar los resúmenes</p></div>';
    }
}

async function refreshSummaries() {
    const refreshBtn = document.getElementById('refreshBtn');
    const loading = document.getElementById('loading');
    const content = document.getElementById('content');
    refreshBtn.disabled = true;
    loading.classList.remove('hidden');
    try {
        const response = await fetch('/refresh', { method: 'POST' });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: { message: 'Error desconocido' } }));
            const errorDetail = errorData.detail || errorData;
            let errorMessage = errorDetail.message || 'Error al actualizar los resúmenes';
            if (errorDetail.instructions) {
                errorMessage += '\n\n' + errorDetail.instructions;
            }
            content.innerHTML = `<div class="empty-state error-state"><h2>❌ Error de Configuración</h2><p>${errorMessage.replace(/\n/g, '<br>')}</p></div>`;
            alert(errorMessage);
            return;
        }
        const data = await response.json();
        summariesData = data;
        renderSummaries();
    } catch (error) {
        console.error('Error refreshing summaries:', error);
        content.innerHTML = '<div class="empty-state error-state"><h2>❌ Error</h2><p>Error al actualizar los resúmenes. Verifica la consola para más detalles.</p></div>';
        alert('Error al actualizar los resúmenes');
    } finally {
        refreshBtn.disabled = false;
        loading.classList.add('hidden');
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-AR', { year: 'numeric', month: 'long', day: 'numeric' });
}

function renderSummaries() {
    const content = document.getElementById('content');
    if (summariesData.length === 0) {
        content.innerHTML = '<div class="empty-state"><p>No hay resúmenes disponibles. Haz click en "Refresh" para obtener los últimos videos.</p></div>';
        return;
    }
    let html = '';
    summariesData.forEach(channel => {
        html += `<div class="channel-section">`;
        html += `<div class="channel-header">`;
        html += `<div class="channel-name">${channel.channel_name}</div>`;
        html += `<a href="${channel.channel_url}" target="_blank" class="channel-url">${channel.channel_url}</a>`;
        html += `</div>`;
        channel.videos.forEach(video => {
            html += `<div class="video-item">`;
            html += `<div class="video-title"><a href="${video.video_url}" target="_blank">${video.title}</a></div>`;
            html += `<div class="video-meta">Publicado: ${formatDate(video.published_at)}</div>`;
            html += `<div class="video-summary">`;
            if (video.has_transcript) {
                if (video.summary && !video.summary.includes("Hubo un error") && !video.summary.includes("No hay transcripción")) {
                    html += `<p>${video.summary}</p>`;
                } else {
                    html += `<p class="error-summary">Hubo un error generando el resumen.</p>`;
                }
            } else {
                html += `<p class="no-transcript">No hay transcripción disponible para este video.</p>`;
            }
            html += `</div>`;
            html += `</div>`;
        });
        html += `</div>`;
    });
    content.innerHTML = html;
}

document.getElementById('refreshBtn').addEventListener('click', refreshSummaries);
loadSummaries();

