// Encapsular en IIFE o Módulo para evitar polución global
// ESTE ARCHIVO AHORA CONTIENE TODA LA LÓGICA DEL EDITOR ROI
const RoiEditor = (function() {

    // --- Variables Internas del Módulo ---
    let canvas = null;
    let polygonMode = { active: false, points: [], drawingLine: null, tempPolygon: null };
    let freehandMode = { active: false, brush: null };
    let currentTool = 'select';
    let historyStack = [];
    let currentStateIndex = -1;

    // --- Constantes de Estilo (Internas) ---
    // Definiciones de ROI_OPTIONS, FREEHAND_ROI_OPTIONS, POINT_OPTIONS, LINE_OPTIONS, TEMP_LINE_OPTIONS
    // (Las mismas que tenías en ambos archivos, las incluimos aquí una sola vez)
    const ROI_OPTIONS = {
        fill: 'rgba(255, 0, 0, 0.3)', // Vermell semi-transparent
        stroke: '#ff0000', // Vermell primari
        strokeWidth: 1.5,
        selectable: true,
        objectCaching: false, // Pot ajudar amb la precisió
        isRoi: true // Propiedad personalizada para identificar nuestras ROIs
    };
    const FREEHAND_ROI_OPTIONS = {
        stroke: 'rgba(255, 0, 0, 0.7)', // Vermell primari semi-transparent per al traç
        fill: 'rgba(255, 0, 0, 0.2)',   // Farciment molt lleuger
        // strokeWidth se definirá dinámicamente
    };
    const POINT_OPTIONS = {
        radius: 4, fill: 'red', originX: 'center', originY: 'center',
        selectable: false, evented: false, isHelper: true // Marcar como a helper
    };
    const LINE_OPTIONS = {
        stroke: 'red', strokeWidth: 1, selectable: false, evented: false, isHelper: true
    };
    const TEMP_LINE_OPTIONS = {
        stroke: 'rgba(255,0,0,0.5)', strokeWidth: 1, selectable: false, evented: false, isHelper: true
    };


    // --- Funciones Privadas (Helpers Internos del Módulo) ---

    // --- Funciones de Manejo de Eventos del Canvas ---
    function _handleRoiMouseDown(options) {
         if (!canvas) return; // Safety check
        const pointer = canvas.getPointer(options.e);
        console.log("[DEBUG] Mouse Down:", pointer, "Tool:", currentTool, "PolygonMode:", polygonMode.active);

        if (polygonMode.active && currentTool === 'polygon') {
            // Comprobar si se hace clic cerca del primer punto para cerrar
            if (polygonMode.points.length > 2) {
                const firstPoint = polygonMode.points[0];
                const distanceThreshold = 10; // Píxeles de tolerancia
                const distance = Math.sqrt(Math.pow(pointer.x - firstPoint.x, 2) + Math.pow(pointer.y - firstPoint.y, 2));
                if (distance < distanceThreshold) {
                    console.log("Closing polygon near start point.");
                    _finishPolygon();
                    return; // Evita añadir el punto de cierre
                }
            }
            // Añadir nuevo punto
            _addPolygonPoint(pointer);
        }
        // No necesitamos manejar 'select' o 'freehand' aquí específicamente, Fabric.js lo hace.
     }

    function _handleRoiMouseMove(options) {
        if (!canvas || !polygonMode.active || polygonMode.points.length === 0 || currentTool !== 'polygon') return;
        const pointer = canvas.getPointer(options.e);
        // Actualizar la línea temporal que sigue al cursor
        if (polygonMode.drawingLine) {
            polygonMode.drawingLine.set({ x2: pointer.x, y2: pointer.y });
            canvas.renderAll();
        }
    }

    function _handleRoiDoubleClick(options) {
        // Finalizar polígono con doble clic si está activo y tiene suficientes puntos
        if (polygonMode.active && currentTool === 'polygon' && polygonMode.points.length >= 3) {
            console.log("Double click detected, finishing polygon.");
            _finishPolygon();
        }
    }

     function _handlePathCreated(e) {
         // Se dispara cuando Fabric.js termina un trazo en modo dibujo libre
         if (freehandMode.active && currentTool === 'freehand') {
             const path = e.path;
             // Aplicar estilos y propiedades ROI al path creado
             path.set({
                 ...ROI_OPTIONS, // Propiedades base como isRoi, selectable
                 ...FREEHAND_ROI_OPTIONS, // Estilos específicos para freehand
                 strokeWidth: canvas.freeDrawingBrush.width, // Usar grosor actual
             });
             path.setCoords(); // Actualizar controles de transformación
             canvas.requestRenderAll();
             _saveHistoryState(); // Guardar el estado
             console.log("Freehand path created and styled with width:", canvas.freeDrawingBrush.width);
         }
     }

    // --- Funciones de Lógica de Dibujo ---
    function _addPolygonPoint(pointer) {
        const point = { x: pointer.x, y: pointer.y };
        polygonMode.points.push(point);

        // Dibuja círculo helper visual en el punto
        const pointCircle = new fabric.Circle({ ...POINT_OPTIONS, left: point.x, top: point.y });
        canvas.add(pointCircle);

        // Dibuja línea helper desde el punto anterior al nuevo
        if (polygonMode.points.length > 1) {
            const prevPoint = polygonMode.points[polygonMode.points.length - 2];
            const line = new fabric.Line([prevPoint.x, prevPoint.y, point.x, point.y], LINE_OPTIONS);
            canvas.add(line);
        }

        // Elimina la línea temporal anterior y crea una nueva desde el punto actual al cursor
        if (polygonMode.drawingLine) canvas.remove(polygonMode.drawingLine);
        polygonMode.drawingLine = new fabric.Line([point.x, point.y, point.x, point.y], TEMP_LINE_OPTIONS);
        canvas.add(polygonMode.drawingLine);

        canvas.requestRenderAll();
        console.log(`Polygon point added: (${point.x.toFixed(1)}, ${point.y.toFixed(1)}). Total points: ${polygonMode.points.length}`);
    }

    function _finishPolygon() {
        if (polygonMode.points.length < 3) {
            console.warn("Need at least 3 points for a polygon. Cancelling.");
            _cleanupPolygonDrawing(); // Limpia los helpers si no se forma polígono
            return;
        }

        // Crea el objeto polígono final de Fabric.js
        const finalPolygon = new fabric.Polygon(polygonMode.points, {
             ...ROI_OPTIONS // Aplica estilos y propiedades ROI
        });
        canvas.add(finalPolygon);

        _cleanupPolygonDrawing(); // Limpia los puntos y líneas helper
        _saveHistoryState(); // Guarda el estado con el nuevo polígono
        console.log("Polygon finished and added.");
        setActiveTool('select'); // Cambiar automáticamente a la herramienta de selección
    }

    function _cleanupPolygonDrawing() {
        if (!canvas) return;
        // Elimina objetos helper (círculos y líneas de puntos)
        canvas.getObjects().forEach(obj => { if (obj.isHelper) canvas.remove(obj); });
        // Elimina la línea temporal que sigue al cursor
        if (polygonMode.drawingLine) canvas.remove(polygonMode.drawingLine);
        // Resetea el estado del modo polígono
        polygonMode.points = [];
        polygonMode.drawingLine = null;
        canvas.requestRenderAll();
        // Ocultar tooltip de ayuda si estaba visible
        const helpTooltip = document.getElementById('polygon-help-roi');
        if(helpTooltip) helpTooltip.style.display = 'none';
    }

    // --- Funciones de Herramientas Adicionales y Teclado ---
    function _deleteSelectedObject() {
        if (!canvas) return;
        const activeObject = canvas.getActiveObject();
        // Solo borrar si hay un objeto activo y es una ROI nuestra
        if (activeObject && activeObject.isRoi) {
            canvas.remove(activeObject);
            canvas.discardActiveObject(); // Deseleccionar
            canvas.requestRenderAll();
            _saveHistoryState(); // Guardar estado tras borrar
            console.log("Selected ROI deleted.");
        } else if (activeObject) {
            console.log("Selected object is not a valid ROI to delete.");
            // Opcional: deseleccionar objetos que no son ROI
            // canvas.discardActiveObject().renderAll();
        } else {
            console.log("No ROI selected for deletion.");
        }
    }

    function _handleKeyDown(e) {
        // Solo actuar si el canvas existe y no estamos en un input/textarea/select
         const activeElement = document.activeElement.tagName;
         const typingInInput = (activeElement === 'INPUT' || activeElement === 'TEXTAREA' || activeElement === 'SELECT');

        // Borrar con Supr/Backspace
        if ((e.key === 'Delete' || e.key === 'Backspace') && canvas && !typingInInput) {
             e.preventDefault(); // Prevenir comportamiento por defecto (ej: navegar atrás)
             _deleteSelectedObject();
        }

        // Deshacer/Rehacer con Ctrl+Z / Ctrl+Y (Cmd en Mac)
        if ((e.ctrlKey || e.metaKey) && !typingInInput) {
            if (e.key === 'z') {
                e.preventDefault();
                _undoLastAction();
            } else if (e.key === 'y') {
                e.preventDefault();
                _redoNextAction();
            }
        }

        // Cancelar dibujo de polígono con ESC
        if (e.key === 'Escape' && polygonMode.active && currentTool === 'polygon' && polygonMode.points.length > 0) {
             e.preventDefault();
             console.log("ESC detected during polygon drawing. Cancelling.");
             _cleanupPolygonDrawing();
             // Podríamos volver a 'select' o dejar 'polygon' activo
             // setActiveTool('select');
        }

         // Atajos de teclado opcionales (S, P, F) - descomentar si se quieren
         /*
         if (!typingInInput && canvas) {
            switch(e.key.toLowerCase()) {
                case 's': setActiveTool('select'); break;
                case 'p': setActiveTool('polygon'); break;
                case 'f': setActiveTool('freehand'); break;
            }
         }
         */
    }

    // --- Funciones de Historial Undo/Redo ---
    function _saveHistoryState() {
        if (!canvas) return;
        // Guardar el estado del canvas como JSON, incluyendo propiedades personalizadas
        const jsonState = canvas.toDatalessJSON(['isRoi', 'isHelper']);
        // Si hemos deshecho y hacemos una nueva acción, eliminamos el historial futuro
        if (currentStateIndex < historyStack.length - 1) {
            historyStack = historyStack.slice(0, currentStateIndex + 1);
        }
        historyStack.push(jsonState);
        currentStateIndex = historyStack.length - 1;
        console.log(`History saved. Index: ${currentStateIndex}, Total states: ${historyStack.length}`);
        _updateUndoRedoButtons(); // Actualizar estado de botones
    }

    function _loadHistoryState(stateIndex) {
        if (!canvas || stateIndex < 0 || stateIndex >= historyStack.length) return;

        const jsonState = historyStack[stateIndex];
        currentStateIndex = stateIndex;

        // Limpiar canvas antes de cargar (evita duplicados si hay error)
        //canvas.clear(); // Esto puede ser problemático con el fondo, mejor usar loadFromJSON directo

        canvas.loadFromJSON(jsonState, () => {
            canvas.renderAll(); // Renderizar el estado cargado
            console.log(`History loaded. Index: ${currentStateIndex}`);

            // Asegurar propiedades después de cargar (loadFromJSON a veces las pierde)
            canvas.getObjects().forEach(obj => {
                 if(obj.isHelper) { obj.selectable = false; obj.evented = false; }
                 if(obj.isRoi) { /* Restaurar otras props si es necesario */ }
            });
            canvas.renderAll(); // Renderizar de nuevo por si cambiaron props

            _updateUndoRedoButtons(); // Actualizar botones
            // Restaurar la herramienta activa asociada a ese estado (opcional)
            // const activeToolForState = historyStack[currentStateIndex]?.tool || 'select';
            // setActiveTool(activeToolForState);
        });
    }

    function _undoLastAction() {
        if (currentStateIndex > 0) { // Solo si no estamos en el estado inicial
            _loadHistoryState(currentStateIndex - 1);
        } else {
            console.log("No more actions to undo.");
        }
    }

    function _redoNextAction() {
        if (currentStateIndex < historyStack.length - 1) { // Solo si no estamos en el último estado
            _loadHistoryState(currentStateIndex + 1);
        } else {
            console.log("No more actions to redo.");
        }
    }

    function _resetHistory() {
        historyStack = [];
        currentStateIndex = -1;
        _updateUndoRedoButtons();
    }

    function _updateUndoRedoButtons() {
        // Habilitar/deshabilitar botones de Undo/Redo según el estado del historial
        const undoBtn = document.getElementById('tool-undo');
        const redoBtn = document.getElementById('tool-redo');
        if (undoBtn) undoBtn.disabled = currentStateIndex <= 0; // Deshabilitar si estamos en el primer estado (o no hay historial)
        if (redoBtn) redoBtn.disabled = currentStateIndex >= historyStack.length - 1; // Deshabilitar si estamos en el último estado
    }

     // --- Funciones de Limpieza y Obtención de Datos ---
     function _clearAllROIs(saveHistory = true) {
         if (!canvas) return;
         let removed = false;
         // Es más seguro obtener los objetos a eliminar primero y luego iterar
         const objectsToRemove = canvas.getObjects().filter(obj => obj.isRoi);
         objectsToRemove.forEach(obj => {
             canvas.remove(obj);
             removed = true;
         });

         if (removed) {
              canvas.renderAll();
              if (saveHistory) _saveHistoryState(); // Guardar estado limpio si se indica
              console.log("All ROIs cleared.");
         }
         // No limpia helpers aquí, se hace al finalizar/cancelar dibujo
     }

    // --- Funciones Públicas del Módulo (Interfaz del Editor) ---

    function initializeRoiEditor(imageUrl) {
         // Limpiar canvas anterior si existe
         if (canvas) {
             // Desvincular listeners globales antes de eliminar el canvas
             document.removeEventListener('keydown', _handleKeyDown);
             canvas.dispose(); // Método de Fabric.js para limpiar memoria y eventos
             canvas = null;
             console.log("Previous canvas disposed.");
         }

         const canvasElement = document.getElementById('roi-canvas');
         const wrapperElement = document.getElementById('canvas-wrapper');
         if (!canvasElement || !wrapperElement) {
             console.error("Canvas elements not found!");
             // Podríamos mostrar un error al usuario aquí
             return;
         }

         // Ajustar tamaño del canvas al contenedor (esto podría necesitar ajustes según CSS)
         canvasElement.width = wrapperElement.clientWidth;
         canvasElement.height = wrapperElement.clientHeight;

         // Crear nueva instancia de Fabric Canvas
         canvas = new fabric.Canvas('roi-canvas', {
            // backgroundColor: '#f0f0f0', // Un fondo ligero para ver los límites
            selection: true, // Habilitar selección por defecto (para la herramienta 'select')
            // Otras opciones de Fabric si son necesarias...
         });
         console.log(`Canvas initialized: ${canvas.width}x${canvas.height}`);

         // Cargar imagen de fondo
         fabric.Image.fromURL(imageUrl, function(img) {
             console.log(`Fabric: Image loaded ok. Original dims: ${img.width}x${img.height}`);
             const maxWidth = canvas.width;
             const maxHeight = canvas.height;
             // Calcular escala para ajustar la imagen al canvas sin exceder tamaño original
             let scale = 1;
             if (img.width > 0 && img.height > 0) {
                scale = Math.min(maxWidth / img.width, maxHeight / img.height, 1);
             } else {
                console.error("Image has invalid dimensions (width or height is 0).");
                scale = 1; // Fallback
             }

             if (!isFinite(scale) || scale <= 0) {
                 console.error("Invalid scale calculated. Using 1.", {maxWidth, maxHeight, imgW: img.width, imgH: img.height});
                 scale = 1;
             }
             console.log(`Fabric: Calculated scale: ${scale}`);

             // Establecer imagen como fondo
             canvas.setBackgroundImage(img, () => {
                 canvas.renderAll(); // Renderizar después de poner fondo
                 console.log("Fabric: Background image set and rendered.");

                 // Asegurar interactividad (a veces Fabric la deshabilita)
                 const upperCanvasEl = canvas.getSelectionElement(); // El canvas superior donde ocurren los eventos
                 if (upperCanvasEl) {
                      upperCanvasEl.style.pointerEvents = 'auto'; // Asegura que recibe clics
                      console.log("Fabric: Set pointer-events: auto on upper-canvas.");
                 } else {
                      console.warn("Fabric: Could not find upper-canvas element.");
                 }

                 // --- ADJUNTAR LISTENERS DEL CANVAS (CLAVE) ---
                 // Desvincular primero por si acaso (re-inicialización)
                 canvas.off('mouse:down');
                 canvas.off('mouse:move');
                 canvas.off('mouse:dblclick');
                 canvas.off('path:created');
                 // Vincular a las funciones INTERNAS del módulo
                 canvas.on('mouse:down', _handleRoiMouseDown);
                 canvas.on('mouse:move', _handleRoiMouseMove);
                 canvas.on('mouse:dblclick', _handleRoiDoubleClick);
                 canvas.on('path:created', _handlePathCreated);
                 console.log("Fabric: Canvas event listeners attached.");

                 // Limpiar ROIs y historial previos
                 _clearAllROIs(false); // No guardar este estado de limpieza inicial
                 _resetHistory();
                 _saveHistoryState(); // Guardar estado inicial (solo fondo)
                 setActiveTool('select'); // Establecer herramienta por defecto

             }, { // Opciones para setBackgroundImage
                 scaleX: scale, scaleY: scale,
                 // Centrar imagen en el canvas
                 top: (maxHeight - img.height * scale) / 2,
                 left: (maxWidth - img.width * scale) / 2,
                 originX: 'left', originY: 'top',
                 selectable: false, evented: false // El fondo no debe ser seleccionable
             });

         }, { // Opciones para fromURL (manejo de CORS si la imagen es de otro dominio)
             crossOrigin: 'anonymous',
             onError: (error) => {
                 console.error("Error loading image with Fabric.js:", error);
                 alert("Error loading image into editor. Please check the console.");
                 // Intentar volver al paso anterior podría ser una opción
                 if (window.navigateStep) window.navigateStep('step-upload');
             }
         });

         // --- ADJUNTAR LISTENER DE TECLADO (CLAVE) ---
         // Asegurarse de que solo hay uno adjunto al documento
         document.removeEventListener('keydown', _handleKeyDown); // Limpiar anterior si existe
         document.addEventListener('keydown', _handleKeyDown); // Adjuntar el interno
         console.log("Document keydown listener attached.");


         // Configurar slider de grosor de pincel (si existe)
         const brushSizeSlider = document.getElementById('brush-size');
         const brushSizeValue = document.getElementById('brush-size-value');
         if (brushSizeSlider && brushSizeValue) {
             // Limpiar listeners antiguos clonando y reemplazando (más seguro)
             const newSlider = brushSizeSlider.cloneNode(true);
             brushSizeSlider.parentNode.replaceChild(newSlider, brushSizeSlider);
             newSlider.addEventListener('input', (e) => {
                 const size = e.target.value;
                 // Aplicar tamaño al pincel de Fabric si está activo
                 if (freehandMode.active && canvas?.freeDrawingBrush) {
                     canvas.freeDrawingBrush.width = parseInt(size, 10);
                 }
                 brushSizeValue.textContent = size; // Actualizar el display numérico
             });
             // Establecer valor inicial en el display
             brushSizeValue.textContent = newSlider.value;
         }
     } // Fin initializeRoiEditor

    function setActiveTool(toolName) {
         // Ignorar si se hace clic en la herramienta ya activa (o manejar como toggle?)
         // if (currentTool === toolName && toolName !== 'delete' && toolName !== 'undo' && toolName !== 'redo') return;

         currentTool = toolName;
         console.log("Switching to tool:", toolName);
         if (!canvas) {
             console.error("Set tool called but canvas is not initialized.");
             return;
         }

         // Resetear estados y configuraciones comunes
         polygonMode.active = false;
         canvas.isDrawingMode = false; // Desactivar modo dibujo libre por defecto
         freehandMode.active = false;
         canvas.selection = false; // Desactivar selección general por defecto
         canvas.defaultCursor = 'default';
         canvas.hoverCursor = 'default'; // O 'move' para selección?
         canvas.discardActiveObject(); // Deseleccionar cualquier objeto activo al cambiar de herramienta
         canvas.requestRenderAll();

         // Ocultar opciones específicas de herramientas
         const freehandOptions = document.getElementById('freehand-options');
         const polygonHelp = document.getElementById('polygon-help-roi');
         if (freehandOptions) freehandOptions.style.display = 'none';
         if (polygonHelp) polygonHelp.style.display = 'none';

         // Limpiar dibujo de polígono incompleto si se cambia de herramienta
         if (toolName !== 'polygon') {
            _cleanupPolygonDrawing();
         }

         // Configurar la herramienta específica
         switch (toolName) {
             case 'select':
                 canvas.selection = true; // Habilitar selección de objetos
                 canvas.defaultCursor = 'default';
                 canvas.hoverCursor = 'move'; // Cursor para mover objetos
                 break;
             case 'polygon':
                 polygonMode.active = true;
                 polygonMode.points = []; // Reiniciar puntos para nuevo polígono
                 canvas.defaultCursor = 'crosshair';
                 canvas.hoverCursor = 'crosshair';
                 if (polygonHelp) polygonHelp.style.display = 'block'; // Mostrar ayuda
                 break;
             case 'freehand':
                 canvas.isDrawingMode = true; // Activar modo dibujo de Fabric
                 freehandMode.active = true;
                 if (!canvas.freeDrawingBrush) {
                     // Usar PencilBrush para trazos simples
                     canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
                 }
                 // Configurar pincel
                 canvas.freeDrawingBrush.color = FREEHAND_ROI_OPTIONS.stroke; // Color del trazo
                 canvas.freeDrawingBrush.width = parseInt(document.getElementById('brush-size')?.value || 3, 10);
                 // canvas.freeDrawingBrush.decimate = 8; // Simplificar trazo (opcional)
                 if (freehandOptions) freehandOptions.style.display = 'block'; // Mostrar opciones de grosor
                 break;
             case 'delete':
                  // No es un 'modo', es una acción. Llamamos a la función y volvemos a 'select'
                  _deleteSelectedObject();
                  // Importante: No seguir al código de actualizar botones para 'delete'
                  // Revertir a 'select' después de borrar
                  setActiveTool('select');
                  return; // Salir para no marcar 'delete' como activo
             case 'undo':
                  // Acción directa
                  _undoLastAction();
                  // Revertir a 'select' o a la herramienta del estado anterior? Mejor 'select'.
                  setActiveTool('select');
                  return;
             case 'redo':
                  // Acción directa
                  _redoNextAction();
                  setActiveTool('select');
                  return;
         }

         // Actualizar estilo visual de los botones de la barra de herramientas
         document.querySelectorAll('.roi-toolbar .tool-button').forEach(btn => {
             btn.classList.remove('active');
             // Marcar como activo el botón correspondiente (si no es una acción puntual)
             if (btn.id === `tool-${currentTool}`) {
                 btn.classList.add('active');
             }
         });
     } // Fin setActiveTool

     function getRoiDataForBackend() {
         if (!canvas || !canvas.backgroundImage) {
              console.error("Canvas or background image not ready for ROI extraction.");
              return []; // Retorna array vacío si no se puede procesar
         }

         const rois = [];
         const background = canvas.backgroundImage;
         // Asegurar valores válidos para escala y offset
         const scaleX = background.scaleX || 1;
         const scaleY = background.scaleY || 1;
         const offsetX = background.left || 0;
         const offsetY = background.top || 0;

         console.log('[DEBUG] Extracting ROIs. Background props:', { scaleX, scaleY, offsetX, offsetY });

         canvas.getObjects().forEach((obj, index) => {
             if (obj.isRoi) { // Procesar solo objetos marcados como ROI
                 let points = [];
                 // Obtener puntos del objeto, aplicando su transformación (posición, escala, rotación)
                 const transformMatrix = obj.calcTransformMatrix();

                 if (obj.type === 'polygon' && obj.points) {
                     // Los puntos del polígono ya están relativos a su origen, aplicar transformación global
                     points = obj.points.map(p => fabric.util.transformPoint({ x: p.x, y: p.y }, transformMatrix));
                 } else if (obj.type === 'path' && obj.path) {
                     // Para paths (dibujo libre), necesitamos extraer los puntos significativos
                     // Esto es una simplificación: toma los puntos finales de cada segmento (M, L, C, Q)
                     // Podría necesitar refinamiento para curvas complejas.
                     points = obj.path.reduce((acc, segment) => {
                         const command = segment[0].toUpperCase();
                         // Tomar el último par de coordenadas del segmento
                         const p = { x: segment[segment.length - 2], y: segment[segment.length - 1] };
                         // Aplicar transformación global al punto extraído
                         acc.push(fabric.util.transformPoint(p, transformMatrix));
                         return acc;
                     }, []);
                 } else {
                      console.warn(`[ROI ${index}] Unsupported ROI object type for export:`, obj.type);
                      return; // Saltar este objeto
                 }

                 // Convertir coordenadas del canvas (transformadas) a coordenadas de la imagen original
                 const originalImagePoints = points.map(p => [
                     Math.round((p.x - offsetX) / scaleX),
                     Math.round((p.y - offsetY) / scaleY)
                 ]);

                 console.log(`[DEBUG] ROI ${rois.length + 1} (${obj.type}): Canvas points (transformed)=`, points.length, `Original points=`, originalImagePoints.length);

                 // Validar que tenemos suficientes puntos y que son válidos
                 if (originalImagePoints.length >= 3) {
                     // Validar si hay NaNs o Infs (puede ocurrir con transformaciones extremas)
                     if(originalImagePoints.some(p => !Number.isFinite(p[0]) || !Number.isFinite(p[1]))) {
                        console.warn(`[ROI ${rois.length + 1}] Ignored due to invalid (NaN/Inf) coordinates after transformation.`);
                     } else {
                        rois.push(originalImagePoints);
                     }
                 } else {
                     console.warn(`[ROI ${rois.length + 1}] Ignored (less than 3 points after processing):`, obj.type, originalImagePoints.length);
                 }
             }
         });
         console.log("[DEBUG] Final ROIs being sent to backend:", JSON.stringify(rois));
         return rois;
     } // Fin getRoiDataForBackend

    // --- Función para configurar los listeners de la Toolbar ---
    // Esta función se llama desde fuera (en DOMContentLoaded)
    function setupToolbarListeners() {
         console.log("Setting up ROI toolbar listeners...");
         // Asegurarse de que los listeners llaman a la función INTERNA setActiveTool
         document.getElementById('tool-select')?.addEventListener('click', () => setActiveTool('select'));
         document.getElementById('tool-polygon')?.addEventListener('click', () => setActiveTool('polygon'));
         document.getElementById('tool-freehand')?.addEventListener('click', () => setActiveTool('freehand'));
         document.getElementById('tool-delete')?.addEventListener('click', () => setActiveTool('delete')); // setActiveTool maneja la acción y revierte a 'select'
         document.getElementById('tool-undo')?.addEventListener('click', () => setActiveTool('undo')); // setActiveTool maneja la acción
         document.getElementById('tool-redo')?.addEventListener('click', () => setActiveTool('redo'));
         // Inicializar estado botones undo/redo
         _updateUndoRedoButtons();
    }

    // --- Interfaz Pública del Módulo `RoiEditor` ---
    // Lo que se devuelve aquí estará accesible desde fuera como RoiEditor.funcion()
    return {
        initialize: initializeRoiEditor,    // Función para iniciar el editor con una imagen
        getRoiData: getRoiDataForBackend,   // Función para obtener las coordenadas ROI para el backend
        setupToolbar: setupToolbarListeners // Función para vincular los botones de la UI
        // No exponemos setActiveTool ni los helpers privados directamente
    };

})(); // Fin IIFE RoiEditor

// --- Lógica Principal de la Aplicación (Fuera del módulo RoiEditor) ---
document.addEventListener('DOMContentLoaded', () => {
     console.log("DOM fully loaded and parsed.");

     // --- Configuración Inicial del Editor ROI ---
     // Vincula los botones de la barra de herramientas a las funciones del módulo RoiEditor
     RoiEditor.setupToolbar(); // <--- Llama a la función expuesta por el módulo

     // --- Estado de la Aplicación y Elementos DOM ---
     const AppState = {
         currentStepId: 'step-upload', // Empieza en el paso de carga
         selectedFile: null,
         imageDataUrl: null // Para pasar al editor ROI
     };

     // Seleccionar elementos del DOM una vez
     const form = document.getElementById('diagnosis-form');
     const uploadZone = document.getElementById('upload-zone');
     const imageInput = document.getElementById('image');
     const fileNameDisplay = document.getElementById('file-name-display');
     const startAnalysisButton = document.getElementById('start-analysis-button');
     const imagePreviewContainer = document.getElementById('image-preview-container');
     const globalErrorDiv = document.getElementById('global-error-message');
     const confirmRoisButton = document.getElementById('confirm-rois-button');
     const roiDataInput = document.getElementById('roi_data'); // Campo hidden

     // --- Funciones de Utilidad (Errores, Navegación, Progreso) ---
     function showGlobalError(message) {
         if (globalErrorDiv) {
             globalErrorDiv.textContent = message;
             globalErrorDiv.style.display = 'block';
         }
         console.error("Global Error:", message);
     }

     function clearGlobalError() {
         if (globalErrorDiv) {
             globalErrorDiv.textContent = '';
             globalErrorDiv.style.display = 'none';
         }
     }

     // Función global para navegar entre pasos (usada en botones onclick y JS)
     window.navigateStep = function(targetStepId) {
         clearGlobalError();
         console.log(`Navigating to step: ${targetStepId}`);
         AppState.currentStepId = targetStepId;

         // Ocultar todos los pasos y activar el objetivo
         document.querySelectorAll('.step-content').forEach(step => step.classList.remove('active'));
         const targetStepElement = document.getElementById(targetStepId);

         if (targetStepElement) {
             targetStepElement.classList.add('active');
             updateProgressBar(targetStepId); // Actualizar barra de progreso visual
             // Scroll suave hacia el inicio del paso activo
             targetStepElement.scrollIntoView({ behavior: 'smooth', block: 'start' });

             // --- INICIALIZACIÓN DEL EDITOR ROI (CLAVE) ---
             // Si navegamos al editor Y tenemos la URL de la imagen
             if (targetStepId === 'step-roi-editor' && AppState.imageDataUrl) {
                 // Usar requestAnimationFrame para asegurar que el elemento es visible antes de inicializar Fabric
                 requestAnimationFrame(() => {
                     console.log("Calling RoiEditor.initialize with image URL...");
                     RoiEditor.initialize(AppState.imageDataUrl); // <--- Llama a la función expuesta por el módulo
                     // Limpiar URL temporal una vez usada (opcional)
                     // AppState.imageDataUrl = null;
                 });
             }
             // Actualizar termómetro si llegamos a resultados
             else if (targetStepId === 'step-results') {
                 // Esperar un poco para que la UI se actualice antes de medir/pintar
                 setTimeout(updateThermometerDisplay, 100);
             }
         } else {
             console.error("Navigation Error: Target step element not found:", targetStepId);
             showGlobalError(`Error interno: No se encontró el paso '${targetStepId}'.`);
         }
     }

     function updateProgressBar(activeStepId) {
         const steps = ['step-upload', 'step-roi-editor', 'step-manual-data', 'step-results'];
         const activeIndex = steps.indexOf(activeStepId);
         document.querySelectorAll('.progress-bar li.step').forEach((li, index) => {
             li.classList.remove('active', 'completed');
             if (index < activeIndex) {
                 li.classList.add('completed');
             } else if (index === activeIndex) {
                 li.classList.add('active');
             }
         });
     }

     // --- Lógica de Carga de Archivo (Upload / Drop) ---
     if (uploadZone && imageInput && startAnalysisButton && fileNameDisplay && imagePreviewContainer) {

         // Listener para el input de archivo (cuando se hace clic y selecciona)
         imageInput.addEventListener('change', handleFileSelect);

         // Listeners para Drag & Drop
         ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
             uploadZone.addEventListener(eventName, preventDefaults, false);
             document.body.addEventListener(eventName, preventDefaults, false); // Prevenir en body también
         });
         ['dragenter', 'dragover'].forEach(eventName => {
             uploadZone.addEventListener(eventName, () => uploadZone.classList.add('dragover'), false);
         });
         ['dragleave', 'drop'].forEach(eventName => {
             uploadZone.addEventListener(eventName, () => uploadZone.classList.remove('dragover'), false);
         });
         uploadZone.addEventListener('drop', handleFileDrop, false);

         // Listener para el botón "Iniciar Análisis"
         startAnalysisButton.addEventListener('click', () => {
             clearGlobalError();
             const fileToProcess = AppState.selectedFile; // Usar el archivo guardado

             if (fileToProcess) {
                 console.log("Start Analysis button clicked. File:", fileToProcess.name);
                 // Asegurarse de que la DataURL está lista (debería estarlo)
                 if (AppState.imageDataUrl) {
                     navigateStep('step-loading'); // Mostrar pantalla de carga
                     // Simular un tiempo de carga o procesamiento antes de ir al editor
                     setTimeout(() => {
                         // La URL ya está en AppState.imageDataUrl
                         console.log("Image data loaded. Navigating to step-roi-editor...");
                         navigateStep('step-roi-editor'); // Navegar al editor
                     }, 500); // Tiempo de espera simulado
                 } else {
                     console.error("AppState.imageDataUrl is null when trying to start analysis.");
                     showGlobalError("Error procesando la previsualización. Intenta seleccionar la imagen de nuevo.");
                     // Resetear estado si falla
                     AppState.selectedFile = null;
                     displayFileNameAndEnableButton(null);
                 }
             } else {
                 console.warn("Start Analysis button clicked, but no valid file stored in AppState.");
                 showGlobalError("Por favor, selecciona o arrastra una imagen válida primero.");
             }
         });

     } else {
         console.error("Error fatal: Elementos de UI para carga de archivos no encontrados.");
         showGlobalError("Error inicializando la página. Refresca o contacta con soporte.");
     }

     // --- Funciones Helper para Carga ---
     function preventDefaults(e) {
         e.preventDefault();
         e.stopPropagation();
     }

     function handleFileSelect(event) {
         clearGlobalError();
         const file = event.target.files[0];
         // ¡Importante! Asignar el archivo al input para que el formulario lo envíe
         // Si el drag & drop no lo hace, hay que buscar otra forma de incluir el File en el POST
         imageInput.files = event.target.files; // Asegura que el form lo incluye
         displayFileNameAndEnableButton(file);
     }

     function handleFileDrop(e) {
         clearGlobalError();
         const dt = e.dataTransfer;
         const file = dt.files[0];
         // Asignar el archivo soltado al input para que el formulario lo envíe
         imageInput.files = dt.files;
         displayFileNameAndEnableButton(file);
     }

     function displayFileNameAndEnableButton(file) {
         clearGlobalError();
         if (file && file.type.startsWith('image/')) {
             fileNameDisplay.textContent = `Archivo: ${file.name}`;
             startAnalysisButton.disabled = false; // Habilitar botón
             AppState.selectedFile = file; // Guardar el objeto File

             // Generar DataURL para preview y editor
             if (imagePreviewContainer) {
                 imagePreviewContainer.innerHTML = ''; // Limpiar preview
                 const img = document.createElement('img');
                 // Estilos básicos para la preview
                 img.style.maxWidth = '100px';
                 img.style.maxHeight = '70px';
                 img.style.borderRadius = '4px';
                 img.style.objectFit = 'cover';

                 const reader = new FileReader();
                 reader.onload = function(e) {
                     img.src = e.target.result;
                     AppState.imageDataUrl = e.target.result; // Guardar DataURL
                     console.log("FileReader success: Image preview ready, DataURL stored.");
                 }
                 reader.onerror = function(e) {
                     console.error("FileReader error:", e);
                     showGlobalError("Error leyendo la previsualización de la imagen.");
                     AppState.imageDataUrl = null; // Limpiar en caso de error
                     startAnalysisButton.disabled = true; // Deshabilitar si falla lectura
                 }
                 reader.readAsDataURL(file); // Iniciar lectura

                 imagePreviewContainer.appendChild(img);
                 imagePreviewContainer.style.display = 'block'; // Mostrar preview
             } else {
                // Si no hay contenedor de preview, no podemos generar/guardar DataURL aquí
                // La lógica de `startAnalysisButton` podría necesitar leer el archivo entonces
                // Pero por ahora, asumimos que imagePreviewContainer existe si se necesita la URL
                console.warn("Image preview container not found. DataURL not generated on file select.");
                AppState.imageDataUrl = null;
                // ¿Deshabilitar botón si la preview es esencial para la URL? Depende del flujo exacto.
             }

         } else {
             // Archivo no válido o no seleccionado
             fileNameDisplay.textContent = file ? `Formato no soportado: ${file.name}` : "";
             startAnalysisButton.disabled = true; // Deshabilitar botón
             AppState.selectedFile = null;
             AppState.imageDataUrl = null;
             if (imagePreviewContainer) {
                 imagePreviewContainer.style.display = 'none';
                 imagePreviewContainer.innerHTML = '';
             }
             if(file) {
                 showGlobalError("Por favor, selecciona un archivo de imagen válido (JPEG, PNG, etc.).");
             }
         }
     }

     // --- Lógica de Confirmación ROI ---
     if (confirmRoisButton && roiDataInput) {
         confirmRoisButton.addEventListener('click', () => {
             clearGlobalError();
             // Obtener datos ROI desde el módulo encapsulado
             const roiDataArray = RoiEditor.getRoiData(); // <--- Llama a la función expuesta

             // Advertir si no hay ROIs, pero permitir continuar
             if (roiDataArray.length === 0) {
                 const proceed = confirm("Advertencia: No has dibujado ninguna Región de Interés (ROI). La puntuación digital será 0. ¿Deseas continuar?");
                 if (!proceed) return; // Detener si el usuario cancela
             }

             // Guardar los datos ROI (como JSON string) en el campo hidden del formulario
             try {
                roiDataInput.value = JSON.stringify(roiDataArray);
                console.log("ROI data set in hidden input:", roiDataInput.value);
                // Navegar al siguiente paso (datos manuales)
                navigateStep('step-manual-data');
                // Abrir la primera pestaña por defecto después de navegar
                setTimeout(() => openTab(null, 'tab-clinical'), 0); // Dar tiempo a que se muestre
             } catch (e) {
                console.error("Error stringifying ROI data:", e);
                showGlobalError("Error interno al procesar las ROIs. Inténtalo de nuevo.");
             }
         });
     } else {
        console.error("Confirm ROIs button or hidden input not found.");
     }

     // --- Lógica de Pestañas (Manual Data) ---
     // Hacer la función accesible globalmente si se usa en `onclick` del HTML
     window.openTab = function(evt, tabName) {
         let i, tabcontent, tablinks;
         tabcontent = document.getElementsByClassName("tab-content");
         for (i = 0; i < tabcontent.length; i++) {
             tabcontent[i].style.display = "none";
             tabcontent[i].classList.remove("active");
         }
         tablinks = document.getElementsByClassName("tab-link");
         for (i = 0; i < tablinks.length; i++) {
             tablinks[i].classList.remove("active");
         }
         const currentTab = document.getElementById(tabName);
         if(currentTab){
             currentTab.style.display = "block";
             currentTab.classList.add("active");
         }
         // Marcar el botón de la pestaña como activo
         const clickedButton = evt ? evt.currentTarget : Array.from(tablinks).find(btn => btn.getAttribute('onclick')?.includes(`'${tabName}'`));
         if (clickedButton) clickedButton.classList.add('active');
     }

     // --- Lógica de Estilos para Selects (Manual Data) ---
     document.querySelectorAll('select.score-select').forEach(select => {
         select.addEventListener('change', function() {
             const selectedOption = this.options[this.selectedIndex];
             // Usar el valor numérico directamente (ya no necesita data-score)
             const score = parseInt(selectedOption.value, 10);
             // Resetear clases de puntuación y aplicar la nueva
             this.className = 'score-select'; // Clase base
             if (!isNaN(score)) {
                  let scoreClass = 'score-unknown';
                  // Aplicar clases basadas en el valor numérico para CSS
                  if (score === 0) scoreClass = 'score-0';
                  else if (score === 1 || score === 2) scoreClass = 'score-1-2'; // Ajustar si CSS lo necesita
                  else if (score === 3) scoreClass = 'score-3';
                  else if (score >= 4) scoreClass = 'score-4-plus';
                  this.classList.add(scoreClass);
             }
         });
         // Disparar evento 'change' al cargar para aplicar estilo inicial
         select.dispatchEvent(new Event('change'));
     });


    // --- Lógica de Resultados (Termómetro) ---
    function updateThermometerDisplay() {
        const thermometer = document.querySelector('.thermometer-display');
        if (!thermometer) return; // Salir si no existe el elemento

        // Leer datos del score desde atributos data-*
        const score = parseInt(thermometer.getAttribute('data-score') || '0', 10);
        const maxScore = parseInt(thermometer.getAttribute('data-max') || '41', 10); // Usar un max por defecto razonable

        // Calcular porcentaje (evitar división por cero)
        const percentage = maxScore > 0 ? Math.min(100, Math.max(0, Math.round((score / maxScore) * 100))) : 0;

        // Seleccionar elementos internos del termómetro
        const fillElement = thermometer.querySelector('.thermometer-fill');
        const bulbElement = thermometer.querySelector('.thermometer-bulb');
        const percentageTextElement = thermometer.querySelector('.thermometer-percentage');

        if (fillElement && bulbElement && percentageTextElement) {
            console.log(`Updating thermometer: Score=${score}, Max=${maxScore}, Percent=${percentage}%`);
            // Actualizar texto y altura del relleno
            percentageTextElement.textContent = `${percentage}%`;
            fillElement.style.height = `${percentage}%`;

            // Determinar color basado en porcentaje (ajustar umbrales según necesidad)
            // Usar variables CSS definidas en style.css si es posible
            let colorVar = 'var(--color-thermo-default)'; // Color por defecto
            if (percentage <= 30) { colorVar = 'var(--color-thermo-low)'; } // Verde
            else if (percentage <= 60) { colorVar = 'var(--color-thermo-medium)'; } // Amarillo/Naranja claro
            else if (percentage <= 85) { colorVar = 'var(--color-thermo-high)'; } // Naranja/Rojo claro
            else { colorVar = 'var(--color-thermo-very-high)'; } // Rojo

            // Aplicar color al relleno y al bulbo
            fillElement.style.backgroundColor = colorVar;
            bulbElement.style.backgroundColor = colorVar;
        } else {
            console.error("Thermometer inner elements not found. Cannot update display.");
        }
    }


     // --- Inicialización de la Aplicación ---
     // Determinar el paso inicial basado en si hay resultados precargados (al venir del POST)
     const resultsSection = document.getElementById('step-results');
     if (resultsSection && resultsSection.classList.contains('active')) {
         // Si la sección de resultados está activa (viene del POST), navegar a ella
         navigateStep('step-results');
     } else {
         // Si no, empezar desde el principio (upload)
         navigateStep('step-upload');
     }

     // Activar la primera pestaña si cargamos directamente en datos manuales (menos común)
     if (document.getElementById('step-manual-data')?.classList.contains('active')) {
         setTimeout(() => openTab(null, 'tab-clinical'), 0);
     }

}); // Fin DOMContentLoaded