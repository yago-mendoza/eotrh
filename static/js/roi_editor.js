// --- Variables Globals per a l'Editor ROI ---
let canvas = null;
let polygonMode = { active: false, points: [], drawingLine: null, tempPolygon: null };
let freehandMode = { active: false, brush: null };
let currentTool = 'select'; // 'select', 'polygon', 'freehand', 'delete'
let historyStack = []; // Per Undo/Redo (simplificat)
let currentStateIndex = -1; // Índex a la pila d'historial

const ROI_OPTIONS = {
    fill: 'rgba(255, 0, 0, 0.3)', // Vermell semi-transparent
    stroke: '#ff0000', // Vermell primari
    strokeWidth: 1.5,
    selectable: true,
    objectCaching: false, // Pot ajudar amb la precisió
    // Propietats personalitzades per identificar les nostres ROIs
    isRoi: true
};

// Afegim opcions específiques per al traç lliure
const FREEHAND_ROI_OPTIONS = {
    stroke: 'rgba(255, 0, 0, 0.7)', // Vermell primari semi-transparent per al traç
    fill: 'rgba(255, 0, 0, 0.2)',   // Farciment molt lleuger o null si es prefereix
    // strokeWidth es definirà dinàmicament
};

const POINT_OPTIONS = {
    radius: 4, fill: 'red', originX: 'center', originY: 'center',
    selectable: false, evented: false, isHelper: true // Marcar com a helper
};

const LINE_OPTIONS = {
    stroke: 'red', strokeWidth: 1, selectable: false, evented: false, isHelper: true
};

const TEMP_LINE_OPTIONS = {
    stroke: 'rgba(255,0,0,0.5)', strokeWidth: 1, selectable: false, evented: false, isHelper: true
};

// --- Inicialització ---
function initializeRoiEditor(imageUrl) {
    if (canvas) {
        // Neteja profunda abans de reutilitzar
        canvas.dispose();
        canvas = null; // Assegura que es crea un de nou
        console.log("Canvas anterior eliminat.");
    }

    const canvasElement = document.getElementById('roi-canvas');
    const wrapperElement = document.getElementById('canvas-wrapper');
    if (!canvasElement || !wrapperElement) {
        console.error("Elements del canvas no trobats!");
        return;
    }

    // Ajustar mida canvas al contenidor (mantenint aspect ratio si cal)
    // Per simplicitat, fem mida fixa o ocupem el contenidor
    canvasElement.width = wrapperElement.clientWidth;
    canvasElement.height = wrapperElement.clientHeight;

    canvas = new fabric.Canvas('roi-canvas', {
        backgroundColor: '#ffffff',
        selection: true,
    });
    console.log(`Canvas inicialitzat amb mida: ${canvas.width}x${canvas.height}`);

    // Carregar la imatge com a fons
    fabric.Image.fromURL(imageUrl, function(img) {
        console.log(`Imatge carregada correctament per Fabric. Dimensions originals: ${img.width}x${img.height}`); // Log Càrrega Imatge OK
        const maxWidth = canvas.width;
        const maxHeight = canvas.height;
        let scale = Math.min(maxWidth / img.width, maxHeight / img.height, 1); // No ampliar més que original

        console.log(`Calculant escala: maxWidth=${maxWidth}, maxHeight=${maxHeight}, img.width=${img.width}, img.height=${img.height} => scale=${scale}`); // Log Càlcul Escala

        // Comprovar si l'escala és vàlida
        if (!isFinite(scale) || scale <= 0) {
            console.error("Error: Escala calculada no vàlida. Comprova dimensions del canvas i la imatge.", {maxWidth, maxHeight, imgWidth: img.width, imgHeight: img.height});
            scale = 1; // Fallback a escala 1 per evitar errors, encara que la imatge no cabrà
        }

        canvas.setBackgroundImage(img, () => { // Funció callback de setBackgroundImage
            canvas.renderAll(); // Renderitza després de posar fons
            console.log("Imatge establerta com a fons i editor ROI inicialitzat.");

            // Get the upper canvas element (used for interaction)
            const upperCanvasEl = canvas.getSelectionElement();
            if (upperCanvasEl) {
                // Ensure the interaction canvas layer is interactive
                upperCanvasEl.style.pointerEvents = 'auto'; // Explicitly enable pointer events
                console.log("[DEBUG] Set pointer-events: auto on upper-canvas element.");

                // Attach a direct click listener for debugging
                console.log("[DEBUG] Trobat upper-canvas. Adjuntant listener de clic directe.");
                upperCanvasEl.removeEventListener('click', handleUpperCanvasClickTest); // Limpiar anterior
                upperCanvasEl.addEventListener('click', handleUpperCanvasClickTest);

            } else {
                 console.error("[ERROR] Could not find upper-canvas element to set pointer-events or attach test listener!");
            }

            // Adjuntem listeners de Fabric
            console.log("[INFO] Adjuntant listeners d'events de Fabric al canvas...");
            canvas.off('mouse:down').on('mouse:down', handleRoiMouseDown);
            canvas.off('mouse:move').on('mouse:move', handleRoiMouseMove);
            canvas.off('mouse:dblclick').on('mouse:dblclick', handleRoiDoubleClick);
            canvas.off('path:created').on('path:created', function(e) {
                 if (freehandMode.active && currentTool === 'freehand') {
                    const path = e.path;
                    path.set({ ...ROI_OPTIONS, stroke: ROI_OPTIONS.stroke, fill: null, isRoi: true });
                    path.setCoords();
                    canvas.requestRenderAll();
                    saveHistoryState();
                    console.log("Path de dibuix lliure creat i estilitzat.");
                }
            });
            console.log("[INFO] Listeners de Fabric adjuntats.");

            // ---> REMOVED OLD LISTENER DE PRUEBA BLOCK <---

            // Neteja qualsevol ROI o estat previ
            clearAllROIs(false);
            resetHistory();
            saveHistoryState(); // Guarda l'estat inicial (només fons)
            setActiveTool('select'); // Eina per defecte

        }, { // Opcions de setBackgroundImage
            scaleX: scale, scaleY: scale,
            top: (maxHeight - img.height * scale) / 2,
            left: (maxWidth - img.width * scale) / 2,
            originX: 'left', originY: 'top',
            selectable: false, evented: false
        });

    }, { // Opcions de fromURL
        crossOrigin: 'anonymous',
        onError: function(error) {
            console.error("Error carregant la imatge amb Fabric.js:", error);
            alert("Hi ha hagut un problema carregant la imatge a l'editor. Comprova la consola per a més detalls.");
            // Podríem intentar tornar al pas anterior o mostrar un missatge a l'usuari
            if (window.navigateStep) window.navigateStep('step-upload');
        }
    });

    // Per gestionar esborrat amb tecla Supr/Del (Aquest pot quedar fora, és del document)
    document.removeEventListener('keydown', handleKeyDown); // Treure anterior per si de cas
    document.addEventListener('keydown', handleKeyDown);

    // Netejar event listener antic si existia per evitar duplicats
    const brushSizeSlider = document.getElementById('brush-size');
    const brushSizeValue = document.getElementById('brush-size-value');
    if (brushSizeSlider) {
        const newSlider = brushSizeSlider.cloneNode(true);
        brushSizeSlider.parentNode.replaceChild(newSlider, brushSizeSlider);
        newSlider.addEventListener('input', (e) => {
            const size = e.target.value;
            if (freehandMode.active && canvas?.freeDrawingBrush) { // Comprovar si canvas existeix
                canvas.freeDrawingBrush.width = parseInt(size, 10);
            }
            if(brushSizeValue) brushSizeValue.textContent = size;
        });
    } else {
         console.warn("Element 'brush-size' no trobat.");
    }
}

// --- Gestió d'Eines ---
function setActiveTool(toolName) {
    currentTool = toolName;
    console.log("Canviant a eina:", toolName);

    // Reset states
    polygonMode.active = false;
    canvas.isDrawingMode = false; // Desactiva mode dibuix lliure per defecte
    freehandMode.active = false;
    canvas.selection = false; // Desactiva selecció per defecte
    canvas.defaultCursor = 'default';
    canvas.hoverCursor = 'default';
    document.getElementById('freehand-options').style.display = 'none';
    document.getElementById('polygon-help-roi').style.display = 'none';

    // Config específica de l'eina
    switch (toolName) {
        case 'select':
            canvas.selection = true;
            canvas.defaultCursor = 'default';
            canvas.hoverCursor = 'move';
            break;
        case 'polygon':
            polygonMode.active = true;
            polygonMode.points = []; // Reinicia punts
            canvas.defaultCursor = 'crosshair';
            canvas.hoverCursor = 'crosshair';
             document.getElementById('polygon-help-roi').style.display = 'block';
            break;
        case 'freehand':
            canvas.isDrawingMode = true;
            freehandMode.active = true;
            if (!canvas.freeDrawingBrush) { // Inicialitza si no existeix
                canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
            }
            canvas.freeDrawingBrush.color = FREEHAND_ROI_OPTIONS.stroke; // Color del contorn ROI
            canvas.freeDrawingBrush.width = parseInt(document.getElementById('brush-size')?.value || 3, 10);
            // Configuracions addicionals del pinzell si cal
            document.getElementById('freehand-options').style.display = 'block';
            break;
        case 'delete':
             // L'esborrat es fa via botó o tecla Supr, no és un mode de cursor
             // Mantenim 'select' actiu per poder seleccionar què esborrar
             currentTool = 'select'; // Tornem a selecció
             canvas.selection = true;
             canvas.defaultCursor = 'default';
             canvas.hoverCursor = 'move';
             // I ara esborrem l'objecte seleccionat
             deleteSelectedObject();
             return; // Ja hem gestionat l'acció
        case 'undo':
             undoLastAction();
             // Torna a l'eina anterior o 'select'
             setActiveTool(historyStack[currentStateIndex]?.tool || 'select');
             return;
        case 'redo':
             redoNextAction();
             setActiveTool(historyStack[currentStateIndex]?.tool || 'select');
             return;

    }

    // Neteja el dibuix de polígon si canviem d'eina
    if (currentTool !== 'polygon') {
        cleanupPolygonDrawing();
    }

    // Actualitza l'estil dels botons
    document.querySelectorAll('.roi-toolbar .tool-button').forEach(btn => {
        btn.classList.remove('active');
        // Marca com actiu el botó corresponent (si no és una acció puntual)
        if (btn.id === `tool-${currentTool}`) {
            btn.classList.add('active');
        }
    });
}

// --- Lògica de Dibuix Polígon ---
function handleRoiMouseDown(options) {
    console.log("[SANITY CHECK] handleRoiMouseDown called. Canvas object:", canvas); // Añadido log
    if (!canvas) return;
    const pointer = canvas.getPointer(options.e);

    if (polygonMode.active) {
        // ---> MODIFICACIÓ 2: Tancament automàtic <---
        if (polygonMode.points.length > 2) { // Necessitem almenys 3 punts per tancar
            const firstPoint = polygonMode.points[0];
            const distanceThreshold = 10; // Píxels de tolerància per tancar
            const distance = Math.sqrt(Math.pow(pointer.x - firstPoint.x, 2) + Math.pow(pointer.y - firstPoint.y, 2));

            if (distance < distanceThreshold) {
                console.log("Detectat clic a prop del punt inicial. Tancant polígon.");
                finishPolygon();
                return; // Important: Evita afegir un nou punt exactamente donde hi ha el primer
            }
        }
        // Si no hem tancat, afegim el punt
        addPolygonPoint(pointer);
    }
}

function handleRoiMouseMove(options) {
    if (!canvas || !polygonMode.active || polygonMode.points.length === 0) return;
    const pointer = canvas.getPointer(options.e);

    // Actualitza la línia temporal
    if (polygonMode.drawingLine) {
        polygonMode.drawingLine.set({ x2: pointer.x, y2: pointer.y });
        canvas.renderAll();
    }
}

function handleRoiDoubleClick(options) {
    if (polygonMode.active && polygonMode.points.length >= 3) {
        finishPolygon();
    }
}

function addPolygonPoint(pointer) {
    const point = { x: pointer.x, y: pointer.y };
    polygonMode.points.push(point);

    // Dibuixa cercle helper
    const pointCircle = new fabric.Circle({ ...POINT_OPTIONS, left: point.x, top: point.y });
    canvas.add(pointCircle);

    // Dibuixa línia helper (des de l'anterior punt)
    if (polygonMode.points.length > 1) {
        const prevPoint = polygonMode.points[polygonMode.points.length - 2];
        const line = new fabric.Line([prevPoint.x, prevPoint.y, point.x, point.y], LINE_OPTIONS);
        canvas.add(line);
    }

    // Prepara/actualitza la línia temporal per al següent segment
    if (polygonMode.drawingLine) canvas.remove(polygonMode.drawingLine);
    polygonMode.drawingLine = new fabric.Line([point.x, point.y, point.x, point.y], TEMP_LINE_OPTIONS);
    canvas.add(polygonMode.drawingLine);

    canvas.requestRenderAll();
}

function finishPolygon() {
    if (polygonMode.points.length < 3) {
        console.warn("Es necessiten almenys 3 punts per a un polígon.");
        cleanupPolygonDrawing();
        return;
    }

    // Crea l'objecte polígon final
    const finalPolygon = new fabric.Polygon(polygonMode.points, {
        ...ROI_OPTIONS // Aplica estils i propietats ROI
    });
    canvas.add(finalPolygon);

    cleanupPolygonDrawing();
    saveHistoryState();
    console.log("Polígon finalitzat i afegit.");
    
    // Canvia automàticament a l'eina de selecció després de tancar el polígon
    setActiveTool('select');
}

function cleanupPolygonDrawing() {
    if (!canvas) return;
    // Elimina objectes helper (identificats per isHelper: true)
    canvas.getObjects().forEach(obj => {
        if (obj.isHelper) {
            canvas.remove(obj);
        }
    });
    if (polygonMode.drawingLine) canvas.remove(polygonMode.drawingLine);
    polygonMode.points = [];
    polygonMode.drawingLine = null;
    canvas.requestRenderAll();
}

// --- Dibuix Lliure ---
// Gestionat majoritàriament per Fabric quan canvas.isDrawingMode = true
// Necessitem capturar quan es crea un path per afegir-li propietats ROI i guardar historial
canvas?.on('path:created', function(e) {
     if (freehandMode.active) {
         const path = e.path;
         // Aplica estils i propietats ROI al path creat
         path.set({
             ...ROI_OPTIONS, // Propietats base com isRoi, selectable
             ...FREEHAND_ROI_OPTIONS, // Estils específics per freehand (stroke, fill transparent)
             strokeWidth: canvas.freeDrawingBrush.width, // Utilitza el gruix actual del pinzell
         });
         path.setCoords(); // Actualitza controls
         canvas.requestRenderAll();
         saveHistoryState(); // Guarda estat després d'afegir path
         console.log("Path de dibuix lliure creat i estilitzat amb gruix:", canvas.freeDrawingBrush.width);
     }
});


// --- Altres Eines ---
function deleteSelectedObject() {
    if (!canvas) return;
    const activeObject = canvas.getActiveObject();
    if (activeObject && activeObject.isRoi) { // Només esborrar si és una ROI nostra
        canvas.remove(activeObject);
        canvas.requestRenderAll();
        saveHistoryState(); // Guarda estat després d'esborrar
        console.log("ROI seleccionada esborrada.");
    } else if (activeObject) {
         console.log("L'objecte seleccionat no és una ROI vàlida per esborrar.");
         // Opcionalment, deseleccionar-lo: canvas.discardActiveObject().renderAll();
    } else {
        console.log("Cap ROI seleccionada per esborrar.");
    }
}

function handleKeyDown(e) {
    // Gestionar tecles Supr/Del per esborrar objecte seleccionat
    if ((e.key === 'Delete' || e.key === 'Backspace') && canvas) {
         const activeObject = canvas.getActiveObject();
         if (activeObject && activeObject.isRoi && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA' && document.activeElement.tagName !== 'SELECT') { // Evita esborrar si s'està editant text i assegura que sigui ROI
             e.preventDefault(); // Evita comportament per defecte (ex: tornar enrere al navegador)
             deleteSelectedObject();
         }
    }
     // Gestió Ctrl+Z / Ctrl+Y
     if (e.ctrlKey || e.metaKey) { // metaKey per a Mac
         if (e.key === 'z') {
             e.preventDefault();
             undoLastAction();
         } else if (e.key === 'y') {
             e.preventDefault();
             redoNextAction();
         }
     }
     // ---> MODIFICACIÓ 4: Cancel·lar Polígon amb ESC <---
     if (e.key === 'Escape' && polygonMode.active && polygonMode.points.length > 0) {
         e.preventDefault(); // Evita altres accions del navegador amb ESC
         console.log("Detectat ESC durant dibuix de polígon. Cancel·lant.");
         cleanupPolygonDrawing();
         // Opcional: tornar a eina 'select'? De moment mantenim 'polygon' actiu.
         // setActiveTool('select');
     }

     // Opcional: Lletres per canviar d'eina (S, P, F)
     if (document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA' && document.activeElement.tagName !== 'SELECT') {
        switch(e.key.toLowerCase()) {
            case 's': setActiveTool('select'); break;
            case 'p': setActiveTool('polygon'); break;
            case 'f': setActiveTool('freehand'); break;
        }
     }
}

// --- Historial Undo/Redo (Simplificat) ---
function saveHistoryState() {
    if (!canvas) return;
    const jsonState = canvas.toDatalessJSON(['isRoi', 'isHelper']);
    if (currentStateIndex < historyStack.length - 1) {
        historyStack = historyStack.slice(0, currentStateIndex + 1);
    }
    historyStack.push(jsonState);
    currentStateIndex = historyStack.length - 1;
    console.log(`Historial guardat. Index: ${currentStateIndex}, Total estats: ${historyStack.length}`);
    updateUndoRedoButtons();
}

function loadHistoryState(stateIndex) {
    if (!canvas || stateIndex < 0 || stateIndex >= historyStack.length) return;
    const jsonState = historyStack[stateIndex];
    currentStateIndex = stateIndex;
    canvas.loadFromJSON(jsonState, () => {
        canvas.renderAll();
        console.log(`Historial carregat. Index: ${currentStateIndex}`);
        // Assegurar que els objectes helper no siguin seleccionables després de carregar
        canvas.getObjects().forEach(obj => {
             if(obj.isHelper) {
                 obj.selectable = false;
                 obj.evented = false;
             }
             if(obj.isRoi) {
                 // Potser restaurar altres propietats si cal
             }
         });
        canvas.renderAll(); // Render final
         updateUndoRedoButtons();
    });
}

function undoLastAction() {
    if (currentStateIndex > 0) { // Només si no estem al primer estat
        loadHistoryState(currentStateIndex - 1);
    } else {
        console.log("No hi ha més accions per desfer.");
    }
}

function redoNextAction() {
    if (currentStateIndex < historyStack.length - 1) { // Només si no estem a l'últim estat
        loadHistoryState(currentStateIndex + 1);
    } else {
        console.log("No hi ha més accions per refer.");
    }
}

function resetHistory() {
     historyStack = [];
     currentStateIndex = -1;
     updateUndoRedoButtons();
}

function updateUndoRedoButtons() {
    document.getElementById('tool-undo').disabled = currentStateIndex <= 0;
    document.getElementById('tool-redo').disabled = currentStateIndex >= historyStack.length - 1;
}

// --- Neteja i Obtenció de Dades ---
function clearAllROIs(saveHistory = true) {
    if (!canvas) return;
    let removed = false;
    canvas.getObjects().forEach(obj => {
        if (obj.isRoi) { // Només esborra ROIs, no helpers ni fons
            canvas.remove(obj);
            removed = true;
        }
    });
    if (removed) {
         canvas.renderAll();
         if (saveHistory) saveHistoryState();
         console.log("Totes les ROIs esborrades.");
    }
    // No neteja helpers aquí, es fa durant el dibuix
}

// Funció per obtenir les dades ROI (igual que abans, però més robusta)
function getRoiDataForBackend() {
    if (!canvas || !canvas.backgroundImage) return []; // Necessita fons per coordenades

    const rois = [];
    const background = canvas.backgroundImage;
    const scaleX = background.scaleX;
    const scaleY = background.scaleY;
    const offsetX = background.left;
    const offsetY = background.top;

    canvas.getObjects().forEach(obj => {
        if (obj.isRoi) { // Només processa objectes marcats com ROI
            let points = [];
            // Simplificació: Tractem polígons i paths (dibuix lliure) obtenint els seus punts
            if (obj.type === 'polygon' && obj.points) {
                 points = obj.points.map(p => {
                     // Aplica transformació de l'objecte (translació, rotació, escala)
                     const point = fabric.util.transformPoint({ x: p.x, y: p.y }, obj.calcTransformMatrix());
                     return point;
                 });
            } else if (obj.type === 'path' && obj.path) {
                 // Extreure punts del path (pot ser una aproximació)
                 // Ens centrem en els punts finals de segments L, Q, C
                 // Ignorem M (moveto inicial) per ara si no és el primer
                 points = obj.path.reduce((acc, segment) => {
                     const command = segment[0].toUpperCase();
                     if (command === 'L' || command === 'C' || command === 'Q' || (command === 'M' && acc.length === 0)) {
                         const p = { x: segment[segment.length - 2], y: segment[segment.length - 1] };
                          // Aplica transformació de l'objecte path
                         acc.push(fabric.util.transformPoint(p, obj.calcTransformMatrix()));
                     }
                     return acc;
                 }, []);
            } else {
                 console.warn("Tipus d'objecte ROI no suportat per exportar:", obj.type);
                 return; // Salta aquest objecte
            }

            // Convertir coordenades del canvas a coordenades de la imatge original
            const originalImagePoints = points.map(p => [
                Math.round((p.x - offsetX) / scaleX),
                Math.round((p.y - offsetY) / scaleY)
            ]);

             // Només afegim si tenim prou punts (mínim 3)
             if (originalImagePoints.length >= 3) {
                 rois.push(originalImagePoints);
             } else {
                 console.warn("ROI ignorada per tenir menys de 3 punts després de processar:", obj.type);
             }
        }
    });
    console.log("ROIs per enviar al backend:", rois);
    return rois;
}

// ---> AÑADIR FUNCIÓN DE PRUEBA <---
function handleUpperCanvasClickTest(event) {
    console.log('[DEBUG] CLIC DETECTAT DIRECTAMENT EN UPPER-CANVAS!', event);
}
// ---> FIN FUNCIÓN DE PRUEBA <---

// --- Vinculació Inicial amb HTML (dins app.js o aquí si és específic de l'editor) ---
document.addEventListener('DOMContentLoaded', () => {
    // Vincula els botons de la barra d'eines ROI
    document.getElementById('tool-select')?.addEventListener('click', () => setActiveTool('select'));
    document.getElementById('tool-polygon')?.addEventListener('click', () => setActiveTool('polygon'));
    document.getElementById('tool-freehand')?.addEventListener('click', () => setActiveTool('freehand'));
    document.getElementById('tool-delete')?.addEventListener('click', () => setActiveTool('delete')); // L'acció es fa dins setActiveTool
    document.getElementById('tool-undo')?.addEventListener('click', () => setActiveTool('undo')); // Acció directa
    document.getElementById('tool-redo')?.addEventListener('click', () => setActiveTool('redo')); // Acció directa

    // Add a test listener to the wrapper
    const wrapperElement = document.getElementById('canvas-wrapper');
    if (wrapperElement) {
        wrapperElement.addEventListener('click', (event) => {
            console.log('[DEBUG] Click detected on #canvas-wrapper! Target:', event.target);
        });
        console.log('[DEBUG] Added direct click listener to #canvas-wrapper.');
    } else {
        console.error('[ERROR] Could not find #canvas-wrapper to attach test listener!');
    }

    // Deshabilita undo/redo inicialment
    updateUndoRedoButtons();
});