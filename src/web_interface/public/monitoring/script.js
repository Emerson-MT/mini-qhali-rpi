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
                    window.location.href = `/monitoring/details/${p.id}`;
                };

                let rawDate = p.date_register || ""; 
                let fechaBonita = "--/--";
                let horaBonita = "--:--";

                // Analizamos el formato: "Sat, 24 Jan 2026 04:50:53 GMT"
                if (rawDate.length > 10) {
                    const partes = rawDate.split(" "); 
                    // partes será: ["Sat,", "24", "Jan", "2026", "04:50:53", "GMT"]

                    if (partes.length >= 5) {
                        // 1. Extraer Día (Índice 1)
                        let dia = partes[1]; 

                        // 2. Extraer y Traducir Mes (Índice 2)
                        const mapaMeses = {
                            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
                            "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
                        };
                        let mesTexto = partes[2];
                        let mes = mapaMeses[mesTexto] || "??";

                        fechaBonita = `${dia}/${mes}`;

                        // 3. Extraer Hora (Índice 4) -> "04:50:53"
                        let horaFull = partes[4];
                        // Quitamos los segundos (tomamos los primeros 5 caracteres)
                        horaBonita = horaFull.substring(0, 5); 
                    }
                }

                row.innerHTML = `
                    <td>${p.lastname}, ${p.name}</td>
                    <td style="text-align: center;">${p.age}</td>
                    <td style="text-align: center;">
                        <span class="tag-sex sex-${p.sex_id}">${p.sex_id}</span>
                    </td>
                    <td>${horaBonita} <small style="color:#666">(${fechaBonita})</small></td>
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