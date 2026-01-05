// --- 1. DATOS DE RESPALDO (FALLBACK) ---
// Los definimos AL PRINCIPIO para que siempre existan, por si falla el fetch.
const backupData = {
    airports: [
        { label: "ATL - Atlanta Municipal", value: "Atlanta Municipal", code: "ATL" },
        { label: "JFK - John F. Kennedy International", value: "John F. Kennedy International", code: "JFK" },
        { label: "LAX - Los Angeles International", value: "Los Angeles International", code: "LAX" },
        { label: "ORD - Chicago O'Hare International", value: "Chicago O'Hare International", code: "ORD" },
        { label: "MIA - Miami International", value: "Miami International", code: "MIA" },
        { label: "SFO - San Francisco International", value: "San Francisco International", code: "SFO" }
    ],
    carriers: [
        { label: "AA - American Airlines Inc.", value: "American Airlines Inc." },
        { label: "DL - Delta Air Lines Inc.", value: "Delta Air Lines Inc." },
        { label: "WN - Southwest Airlines Co.", value: "Southwest Airlines Co." },
        { label: "UA - United Air Lines Inc.", value: "United Air Lines Inc." },
        { label: "B6 - JetBlue Airways", value: "JetBlue Airways" }
    ]
};

// --- 2. FUNCIÓN DE AUTOCOMPLETE ---
function setupAutocomplete(inputId, listId, hiddenId, dataArray) {
    const input = document.getElementById(inputId);
    const list = document.getElementById(listId);
    const hidden = document.getElementById(hiddenId);

    if (!input || !list || !hidden) return; // Protección contra errores

    input.addEventListener("input", function() {
        const val = this.value.toUpperCase();
        list.innerHTML = ""; 
        if (!val) return;

        const matches = dataArray.filter(item => {
            return item.label.toUpperCase().includes(val) || (item.code && item.code.includes(val));
        });

        matches.forEach(item => {
            const div = document.createElement("div");
            div.innerHTML = item.label.replace(new RegExp(val, "gi"), (match) => `<strong>${match}</strong>`);
            
            div.addEventListener("click", function() {
                input.value = item.label; 
                hidden.value = item.value; 
                list.innerHTML = ""; 
            });
            list.appendChild(div);
        });
    });

    document.addEventListener("click", function(e) {
        if (e.target !== input) list.innerHTML = "";
    });
}

// --- 3. CARGA DE DATOS (Lógica Corregida) ---
console.log("Intentando cargar datos...");

fetch('assets/frontend_options.json') // Asegúrate de que la ruta sea correcta
    .then(response => {
        if (!response.ok) throw new Error("No se pudo cargar JSON externo");
        return response.json();
    })
    .then(data => {
        console.log("✅ Datos cargados desde JSON externo.");
        // CAMINO FELIZ: Inicializamos con los datos del archivo
        setupAutocomplete("airport-input", "airport-list", "airport-real-value", data.airports);
        setupAutocomplete("carrier-input", "carrier-list", "carrier-real-value", data.carriers);
    })
    .catch(error => {
        console.warn("⚠️ Falló la carga del JSON (¿CORS?). Usando datos de respaldo.", error);
        // CAMINO DE ERROR: Inicializamos con backupData
        setupAutocomplete("airport-input", "airport-list", "airport-real-value", backupData.airports);
        setupAutocomplete("carrier-input", "carrier-list", "carrier-real-value", backupData.carriers);
    });


// --- 4. LÓGICA DE SUBMIT (CONEXIÓN AL BACKEND) ---
const form = document.getElementById("predictionForm");

if (form) {
    form.addEventListener("submit", async function(e) {
        e.preventDefault(); 

        const btn = document.querySelector(".btn-predict");
        const loader = document.getElementById("loader");
        const resultBox = document.getElementById("result");
        
        btn.style.display = "none";
        loader.style.display = "block";
        resultBox.style.display = "none";

        const carrierReal = document.getElementById("carrier-real-value").value;
        const airportReal = document.getElementById("airport-real-value").value;
        const date = document.getElementById("date-input").value; 
        const time = document.getElementById("time-input").value; 

        try {
            // LLAMADA AL BACKEND REAL
            const response = await fetch("http://127.0.0.1:8000/predict", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    CARRIER_NAME: carrierReal,
                    DEPARTING_AIRPORT: airportReal,
                    FECHA: date,
                    HORA: time
                })
            });

            if (!response.ok) throw new Error("Error en la API");
            const data = await response.json();

            loader.style.display = "none";
            btn.style.display = "block";
            
            const isDelayed = data.prediction === "RETRASADO";
            const probPercent = (data.probability * 100).toFixed(0);

            resultBox.style.display = "block";
            resultBox.className = "result-box " + (isDelayed ? "result-danger" : "result-safe");
            
            document.getElementById("result-title").innerText = isDelayed ? "⚠️ ALTO RIESGO" : "✅ PUNTUAL";
            document.getElementById("result-percent").innerText = probPercent + "%";
            document.getElementById("result-msg").innerText = data.details || "Cálculo completado.";

        } catch (error) {
            console.error(error);
            loader.style.display = "none";
            btn.style.display = "block";
            alert("Error conectando con el servidor. Asegúrate de que 'main.py' esté corriendo.");
        }
    });
}

// Poner fecha de hoy por defecto
const dateInput = document.getElementById("date-input");
if(dateInput) dateInput.valueAsDate = new Date();