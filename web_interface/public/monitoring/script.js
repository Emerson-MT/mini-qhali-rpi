// monitoring/script.js

let currentPage = 1;
let debounceTimer;

document.addEventListener("DOMContentLoaded", () => {
    fetchPatients();
    startClock();
    
    // Escuchar cambios en el buscador
    document.getElementById('searchInput').addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        // Esperar 500ms antes de buscar para no saturar la BD
        debounceTimer = setTimeout(() => {
            currentPage = 1; // Resetear a página 1 al buscar
            fetchPatients(e.target.value);
        }, 500);
    });
});

async function fetchPatients(searchTerm = "") {
    const tableBody = document.getElementById('patientsTableBody');
    const loading = document.getElementById('loading');
    const noData = document.getElementById('noData');
    
    // UI Estado de carga
    tableBody.innerHTML = "";
    loading.style.display = "block";
    noData.style.display = "none";

    try {
        // Llamada a TU API Python
        const response = await fetch(`/api/pacientes?page=${currentPage}&search=${encodeURIComponent(searchTerm)}`);
        const result = await response.json();

        loading.style.display = "none";

        if (result.status === "success") {
            const pacientes = result.data;
            
            if (pacientes.length === 0) {
                noData.style.display = "block";
                updatePagination(0);
                return;
            }

            // Renderizar Filas
            pacientes.forEach(p => {
                const row = document.createElement('tr');

                row.style.cursor = "pointer"; 
                row.onclick = () => {
                    // Redirige a la nueva ruta usando el ID del paciente
                    window.location.href = `/monitoring/details/${p.id}`;
                };
                
                // Formatear fecha (Ej: 14:11 pm - 12/01)
                const dateObj = new Date(p.date_register); // Asegúrate que tu DB retorna formato ISO o compatible
                const timeStr = dateObj.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit', hour12: true });
                const dateStr = dateObj.toLocaleDateString('es-PE', { day: '2-digit', month: '2-digit' });

                row.innerHTML = `
                    <td>${p.lastname}, ${p.name}</td>
                    <td style="text-align: center;">${p.age}</td>
                    <td style="text-align: center;">
                        <span class="tag-sex sex-${p.sex_id}">${p.sex_id}</span>
                    </td>
                    <td>${timeStr} <small style="color:#666">(${dateStr})</small></td>
                `;
                tableBody.appendChild(row);
            });

            updatePagination(result.total_pages);
        } else {
            console.error("Error backend:", result.message);
            loading.innerText = "Error cargando datos.";
        }

    } catch (error) {
        console.error("Error red:", error);
        loading.style.display = "none";
        loading.innerText = "Error de conexión.";
    }
}

function updatePagination(totalPages) {
    const btnPrev = document.getElementById('btnPrev');
    const btnNext = document.getElementById('btnNext');
    const pageIndicator = document.getElementById('pageIndicator');

    pageIndicator.innerText = `Pág ${currentPage} de ${totalPages || 1}`;

    btnPrev.disabled = (currentPage <= 1);
    btnNext.disabled = (currentPage >= totalPages || totalPages === 0);
}

function changePage(direction) {
    currentPage += direction;
    const searchTerm = document.getElementById('searchInput').value;
    fetchPatients(searchTerm);
}

function startClock() {
    const clock = document.getElementById('clock');
    setInterval(() => {
        const now = new Date();
        clock.innerText = now.toLocaleTimeString('es-PE', { hour12: true });
    }, 1000);
}