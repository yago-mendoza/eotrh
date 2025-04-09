document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('diagnosis-form');
    const uploadZone = document.getElementById('upload-zone');
    const imageInput = document.getElementById('image');
    const fileNameDisplay = document.getElementById('file-name-display');
    const startAnalysisButton = document.getElementById('start-analysis-button');
    let currentStep = 1; // Comencem a la pujada
    let imageDataForRoiEditor = null; // Variable per guardar temporalment la URL

    // --- Navegació per Passos ---
    window.navigateStep = function(targetStepId, skipHistory = false) { // Permet saltar historial per Undo/Redo
        console.log(`Navegant a: ${targetStepId}`);
        // Oculta tots els passos
        document.querySelectorAll('.step-content').forEach(step => step.classList.remove('active'));
        // Mostra el pas desitjat
        const targetStepElement = document.getElementById(targetStepId);
        if (targetStepElement) {
            targetStepElement.classList.add('active');
            // Actualitza la barra de progrés
            updateProgressBar(targetStepId);
            // Scroll cap a dalt de la pàgina o del pas?
            // window.scrollTo(0, 0);
            targetStepElement.scrollIntoView({ behavior: 'smooth', block: 'start' });

            // *** NOU: Inicialitza l'editor ROI DESPRÉS de mostrar el pas ***
            if (targetStepId === 'step-roi-editor' && imageDataForRoiEditor) {
                 // Usem requestAnimationFrame per esperar que el navegador calculi dimensions
                 requestAnimationFrame(() => {
                    console.log("Calling initializeRoiEditor AFTER step is active...");
                    initializeRoiEditor(imageDataForRoiEditor); // Funció de roi_editor.js
                    imageDataForRoiEditor = null; // Neteja la variable temporal
                 });
            }
            // Si arribem als resultats, inicialitzem el gauge (si existeix)
            else if (targetStepId === 'step-results') {
                 // Esperem un petit instant per assegurar que tot està renderitzat
                 setTimeout(updateThermometerDisplay, 50); 
            }

        } else {
            console.error("Error: El pas objectiu no existeix:", targetStepId);
        }
    }

    function updateProgressBar(activeStepId) {
        const steps = ['step-upload', 'step-roi-editor', 'step-manual-data', 'step-results'];
        const activeIndex = steps.indexOf(activeStepId);
        currentStep = activeIndex + 1; // Actualitza el pas actual

        document.querySelectorAll('.progress-bar li.step').forEach((li, index) => {
            li.classList.remove('active', 'completed');
            if (index < activeIndex) {
                li.classList.add('completed');
            } else if (index === activeIndex) {
                li.classList.add('active');
            }
        });
    }

    // --- Pas 0: Drag & Drop i Pujada ---
    if (uploadZone && imageInput && startAnalysisButton) {
        // Ya no necesitamos el evento click en uploadZone, el label lo maneja automáticamente
        
        imageInput.addEventListener('change', handleFileSelect);

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadZone.addEventListener(eventName, () => uploadZone.classList.add('dragover'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, () => uploadZone.classList.remove('dragover'), false);
        });

        uploadZone.addEventListener('drop', handleFileDrop, false);

        startAnalysisButton.addEventListener('click', () => {
            const file = imageInput.files[0];
            if (file) {
                console.log("Start Analysis button clicked. File:", file.name); // Log 1: Button clicked
                // 1. Mostra pantalla de càrrega
                navigateStep('step-loading');

                // 2. Simula càrrega i inicialitza editor ROI
                setTimeout(() => {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        console.log("FileReader onload event triggered."); // Log 2: File read
                        const imageDataUrl = e.target.result;
                        // Log 3: Check if imageDataUrl looks like a data URL (optional, can be very long)
                        console.log("Image data URL length:", imageDataUrl ? imageDataUrl.length : 'null');
                        // console.log("Image data URL (first 100 chars):", imageDataUrl ? imageDataUrl.substring(0, 100) : 'null');

                        // *** NOU: Guarda la URL i navega, l'inicialització es farà a navigateStep ***
                        imageDataForRoiEditor = imageDataUrl; // Guarda la URL
                        console.log("Image data stored. Navigating to step-roi-editor..."); // Log 4 (modificat)
                        navigateStep('step-roi-editor'); // Navega a l'editor (que ara cridarà initializeRoiEditor)
                    }
                    reader.onerror = function(e) { // Add error handling for FileReader
                        console.error("FileReader error:", e);
                        alert("Error llegint el fitxer d'imatge.");
                        navigateStep('step-upload'); // Go back to upload step on error
                    }
                    console.log("Reading file as Data URL..."); // Log 6: Before reading file
                    reader.readAsDataURL(file);
                }, 1500); // Temps de càrrega simulat (1.5 segons)
            } else {
                console.warn("Start Analysis button clicked, but no file selected."); // Log 7: No file selected
            }
        });
    }

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function handleFileSelect(event) {
        const file = event.target.files[0];
        displayFileNameAndEnableButton(file);
    }

    function handleFileDrop(e) {
        const dt = e.dataTransfer;
        const file = dt.files[0];
        displayFileNameAndEnableButton(file);
        // Assigna el fitxer a l'input per si l'usuari no fa clic a "Iniciar"
        if(imageInput && dt.files.length > 0) {
            imageInput.files = dt.files;
        }
    }

    function displayFileNameAndEnableButton(file) {
        if (file && file.type.startsWith('image/')) {
            fileNameDisplay.textContent = `Fitxer seleccionat: ${file.name}`;
            startAnalysisButton.disabled = false;
            
            // Afegim previsualització de la imatge
            const previewContainer = document.getElementById('image-preview-container');
            if (previewContainer) {
                // Netejem el contenidor primer
                previewContainer.innerHTML = '';
                
                // Creem una previsualització de la imatge
                const img = document.createElement('img');
                img.style.maxWidth = '75px';
                img.style.maxHeight = '45px';
                img.style.borderRadius = '8px';
                img.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
                
                // Llegim el fitxer i l'assignem com a src
                const reader = new FileReader();
                reader.onload = function(e) {
                    img.src = e.target.result;
                };
                reader.readAsDataURL(file);
                
                // Afegim la imatge al contenidor i mostrem el contenidor
                previewContainer.appendChild(img);
                previewContainer.style.display = 'block';
            }
        } else {
            fileNameDisplay.textContent = "Format d'imatge no vàlid.";
            startAnalysisButton.disabled = true;
            
            // Amaguem la previsualització si hi ha un error
            const previewContainer = document.getElementById('image-preview-container');
            if (previewContainer) {
                previewContainer.style.display = 'none';
                previewContainer.innerHTML = '';
            }
        }
    }

    // --- Pas 1: Editor ROI ---
    const confirmRoisButton = document.getElementById('confirm-rois-button');
    if (confirmRoisButton) {
        confirmRoisButton.addEventListener('click', () => {
            const roiDataArray = getRoiDataForBackend(); // Funció de roi_editor.js
            if (roiDataArray.length === 0) {
                const proceed = confirm("No has seleccionat cap Regió d'Interès (ROI). Això pot afectar els resultats de l'anàlisi. Vols continuar igualment?");
                if (!proceed) return;
            }
            // Guarda les dades ROI al camp ocult
            document.getElementById('roi_data').value = JSON.stringify(roiDataArray);
            // Navega al pas de dades manuals
            navigateStep('step-manual-data');
            // Activa la primera pestanya per defecte
            openTab(null, 'tab-clinical'); // Passa null per event si no cal
        });
    }


    // --- Pas 2: Dades Manuals (Tabs i Score Highlighting) ---
    window.openTab = function(evt, tabName) { // Fes-la global per onclick HTML
        let i, tabcontent, tablinks;
        tabcontent = document.getElementsByClassName("tab-content");
        for (i = 0; i < tabcontent.length; i++) {
            tabcontent[i].style.display = "none";
            tabcontent[i].classList.remove("active"); // Treu classe activa
        }
        tablinks = document.getElementsByClassName("tab-link");
        for (i = 0; i < tablinks.length; i++) {
            tablinks[i].classList.remove("active");
        }
        const currentTab = document.getElementById(tabName);
        if(currentTab){
            currentTab.style.display = "block";
            currentTab.classList.add("active"); // Marca contingut actiu
        }

        if (evt && evt.currentTarget) {
            evt.currentTarget.classList.add("active");
        } else {
            // Busca botó per nom si no hi ha event
            const activeButton = Array.from(tablinks).find(btn => btn.getAttribute('onclick')?.includes(`'${tabName}'`));
            if (activeButton) activeButton.classList.add('active');
        }
    }

    // Afegeix listeners als selects per canviar el color/estil
    document.querySelectorAll('select.score-select').forEach(select => {
        select.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const score = selectedOption.getAttribute('data-score');
            // Treu classes de puntuació anteriors
            this.className = 'score-select'; // Reset a classe base
            // Afegeix nova classe de puntuació si existeix
            if (score !== null) {
                 // Determina la classe basada en la puntuació
                 let scoreClass = 'score-unknown';
                 const scoreNum = parseInt(score, 10);
                 if (scoreNum === 0) scoreClass = 'score-0';
                 else if (scoreNum === 1 || scoreNum === 2) scoreClass = 'score-1'; // O score-1-2
                 else if (scoreNum === 3) scoreClass = 'score-3';
                 else if (scoreNum >= 4) scoreClass = 'score-4';
                 this.classList.add(scoreClass);
            }
        });
        // Dispara 'change' inicialment per aplicar estil a la selecció per defecte
        select.dispatchEvent(new Event('change'));
    });

    // --- Pas 3: Resultats (Actualització Termòmetre) ---
    function updateThermometerDisplay() {
        const thermometer = document.querySelector('.thermometer-display');
        if (!thermometer) return; // Si no hi ha termòmetre, no fem res

        const score = parseInt(thermometer.getAttribute('data-score') || '0', 10);
        const maxScore = parseInt(thermometer.getAttribute('data-max') || '41', 10);
        const percentage = maxScore > 0 ? Math.round((score / maxScore) * 100) : 0;

        const fillElement = thermometer.querySelector('.thermometer-fill');
        const bulbElement = thermometer.querySelector('.thermometer-bulb');
        const percentageTextElement = thermometer.querySelector('.thermometer-percentage');

        if (fillElement && bulbElement && percentageTextElement) {
            console.log(`Actualitzant termòmetre: Score=${score}, Max=${maxScore}, Percent=${percentage}%`);
            
            // 1. Actualitza el text del percentatge (ja fet a HTML, però confirmem)
            percentageTextElement.textContent = `${percentage}%`;

            // 2. Actualitza l'altura del farcit
            fillElement.style.height = `${percentage}%`;

            // 3. Actualitza el color basat en la puntuació (similar a classification-text)
            let colorClass = '';
            let colorVar = 'var(--medium-text)'; // Color per defecte
            if (score <= 12) { 
                colorClass = 'low-risk'; 
                colorVar = 'var(--success-color)'; // Verd
            } else if (score <= 25) { 
                colorClass = 'moderate-risk';
                colorVar = 'var(--warning-color)'; // Groc
            } else if (score <= 34) { 
                colorClass = 'high-risk';
                colorVar = 'orange'; // Taronja (igual que selects)
            } else { 
                colorClass = 'very-high-risk';
                colorVar = 'var(--danger-color)'; // Vermell
            }
            
            fillElement.style.backgroundColor = colorVar;
            bulbElement.style.backgroundColor = colorVar;
            
            // Podríem també actualitzar la classe de classification-text aquí si no ve del backend
            const classificationText = document.getElementById('classification-text-id');
            if (classificationText) {
                 classificationText.className = 'classification-text'; // Reset
                 if (colorClass) classificationText.classList.add(colorClass);
             }

        } else {
            console.error("Elements del termòmetre no trobats.");
        }
    }

    // --- Inicialització General ---
    // Comprova si hi ha resultats per mostrar directament aquest pas
     const resultsSection = document.getElementById('step-results');
     if (resultsSection && resultsSection.classList.contains('active')) {
        navigateStep('step-results'); // Assegura que la barra i tot està correcte
     } else {
         navigateStep('step-upload'); // Comença pel primer pas
     }

     // Activa la primera pestanya si naveguem a dades manuals
     if (document.getElementById('step-manual-data').classList.contains('active')) {
         openTab(null, 'tab-clinical');
     }

}); // Fi DOMContentLoaded