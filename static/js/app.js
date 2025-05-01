// Encapsular en IIFE o Módulo para evitar polución global y crear un scope privado.
// OBJETIVO: Centralizar toda la lógica del editor de Regiones de Interés (ROI).
// ORIGEN: Este módulo reemplaza a los antiguos 'roi_editor.js' y 'roi_selector.js'.
const RoiEditor = (function() {

    // --- Variables Internas del Módulo (Estado Privado) ---
    // Estas variables mantienen el estado del editor y no son accesibles desde fuera.
    let canvas = null; // Referencia a la instancia de Fabric.js Canvas. Null hasta la inicialización.
    // Estado específico para la herramienta de dibujo de polígonos.
    let polygonMode = {
        active: false,      // ¿Está la herramienta polígono activa?
        points: [],         // Array de coordenadas {x, y} de los vértices dibujados hasta ahora (en coords del canvas).
        drawingLine: null,  // Línea temporal que sigue al cursor desde el último punto.
        tempPolygon: null   // Polígono temporal (actualmente no usado, podría usarse para previsualización).
    };
    // Estado específico para la herramienta de dibujo a mano alzada.
    let freehandMode = {
        active: false, // ¿Está la herramienta de mano alzada activa?
        brush: null    // Referencia al pincel de Fabric.js (configurado en setActiveTool).
    };
    let currentTool = 'select'; // Herramienta activa actualmente ('select', 'polygon', 'freehand').
    let historyStack = [];      // Array para almacenar los estados del canvas (serializados a JSON) para Deshacer/Rehacer.
    let currentStateIndex = -1; // Índice del estado actual en historyStack (-1 si está vacío).

    // --- Constantes de Estilo (Configuración Visual Interna) ---
    // Define la apariencia de las ROIs y los elementos de ayuda visual.
    // POR QUÉ: Centralizar estilos facilita cambios y consistencia.

    // Estilos para las ROIs finales (Polígonos y Trazos a Mano Alzada base).
    const ROI_OPTIONS = {
        fill: 'rgba(255, 0, 0, 0.3)', // Relleno rojo semi-transparente.
        stroke: '#ff0000',           // Borde rojo opaco.
        strokeWidth: 1.5,            // Grosor del borde.
        selectable: true,            // Permite seleccionar la ROI con la herramienta 'select'.
        objectCaching: false,        // Desactivar caché de objetos puede mejorar la precisión en algunas interacciones.
        // *** Propiedad Clave ***
        isRoi: true                  // Propiedad personalizada para IDENTIFICAR objetos que son ROIs.
                                     // USADA EN: getRoiDataForBackend para filtrar qué exportar,
                                     //          _deleteSelectedObject para saber qué borrar.
    };
    // Estilos específicos adicionales para ROIs creadas a mano alzada.
    const FREEHAND_ROI_OPTIONS = {
        stroke: 'rgba(255, 0, 0, 0.7)', // Borde un poco más opaco para visibilidad.
        fill: 'rgba(255, 0, 0, 0.2)',   // Relleno muy ligero.
        // strokeWidth se aplicará dinámicamente basado en el slider del pincel.
    };
    // Estilos para los círculos visuales que marcan los vértices del polígono durante el dibujo.
    const POINT_OPTIONS = {
        radius: 4, fill: 'red', originX: 'center', originY: 'center',
        selectable: false, evented: false, // No interactivos.
        isHelper: true // Propiedad personalizada para identificar elementos de ayuda. USADA EN: _cleanupPolygonDrawing.
    };
    // Estilos para las líneas que conectan los vértices del polígono durante el dibujo.
    const LINE_OPTIONS = {
        stroke: 'red', strokeWidth: 1, selectable: false, evented: false,
        isHelper: true // Identificador de helper. USADA EN: _cleanupPolygonDrawing.
    };
    // Estilos para la línea temporal que va del último vértice al cursor durante el dibujo del polígono.
    const TEMP_LINE_OPTIONS = {
        stroke: 'rgba(255,0,0,0.5)', strokeWidth: 1, selectable: false, evented: false,
        isHelper: true // Identificador de helper. USADA EN: _cleanupPolygonDrawing.
    };


    // --- Funciones Privadas (Helpers Internos del Módulo) ---
    // Estas funciones implementan la lógica interna y son llamadas por los manejadores de eventos o funciones públicas.

    // --- Funciones de Manejo de Eventos del Canvas ---
    // Se adjuntan al canvas de Fabric en `initializeRoiEditor`.

    /**
     * Manejador para el evento 'mouse:down' (clic del ratón).
     * OBJETIVO: Añadir puntos al polígono o finalizarlo.
     * CÓMO: Comprueba si la herramienta 'polygon' está activa.
     *       Si sí, determina si el clic es cerca del primer punto (para cerrar) o si añade un nuevo punto.
     * POR QUÉ NO OTROS MODOS: Fabric.js maneja la selección ('select') y el inicio del dibujo ('freehand') internamente.
     */
    function _handleRoiMouseDown(options) {
         if (!canvas) return; // Comprobación de seguridad.
        const pointer = canvas.getPointer(options.e);
        // console.log("[DEBUG] Mouse Down:", pointer, "Tool:", currentTool, "PolygonMode:", polygonMode.active);

        if (polygonMode.active && currentTool === 'polygon') {
            if (polygonMode.points.length > 2) {
                const firstPoint = polygonMode.points[0];
                const distanceThreshold = 10;
                const distance = Math.sqrt(Math.pow(pointer.x - firstPoint.x, 2) + Math.pow(pointer.y - firstPoint.y, 2));
                if (distance < distanceThreshold) {
                    // console.log("Closing polygon near start point.");
                    _finishPolygon();
                    return;
                }
            }
            _addPolygonPoint(pointer);
        }
     }

    function _handleRoiMouseMove(options) {
        if (!canvas || !polygonMode.active || polygonMode.points.length === 0 || currentTool !== 'polygon') return;
        const pointer = canvas.getPointer(options.e);
        if (polygonMode.drawingLine) {
            polygonMode.drawingLine.set({ x2: pointer.x, y2: pointer.y });
            canvas.renderAll();
        }
    }

    function _handleRoiDoubleClick(options) {
        if (polygonMode.active && currentTool === 'polygon' && polygonMode.points.length >= 3) {
            // console.log("Double click detected, finishing polygon.");
            _finishPolygon();
        }
    }

     function _handlePathCreated(e) {
         if (freehandMode.active && currentTool === 'freehand') {
             const path = e.path;
             path.set({
                 ...ROI_OPTIONS,
                 ...FREEHAND_ROI_OPTIONS,
                 strokeWidth: canvas.freeDrawingBrush.width,
             });
             path.setCoords();
             canvas.requestRenderAll();
             _saveHistoryState();
             // console.log("Freehand path created and styled with width:", canvas.freeDrawingBrush.width);
         }
     }

    // --- Funciones de Lógica de Dibujo ---

    /**
     * Añade un nuevo vértice al polígono que se está dibujando.
     * OBJETIVO: Registrar el punto y actualizar la ayuda visual.
     * CÓMO:
     *   1. Añade las coordenadas (en el sistema del canvas) al array `polygonMode.points`.
     *   2. Dibuja un círculo visual (`POINT_OPTIONS`) en el punto (marcado como `isHelper: true`).
     *   3. Si hay más de un punto, dibuja una línea visual (`LINE_OPTIONS`) desde el penúltimo al nuevo punto (`isHelper: true`).
     *   4. Elimina la línea temporal anterior (`polygonMode.drawingLine`).
     *   5. Crea una nueva línea temporal (`TEMP_LINE_OPTIONS`) desde el nuevo punto hasta sí mismo (se actualizará en `_handleRoiMouseMove`) (`isHelper: true`).
     *   6. Solicita redibujo del canvas.
     */
    function _addPolygonPoint(pointer) {
        const point = { x: pointer.x, y: pointer.y };
        polygonMode.points.push(point);

        const pointCircle = new fabric.Circle({ ...POINT_OPTIONS, left: point.x, top: point.y });
        canvas.add(pointCircle);

        if (polygonMode.points.length > 1) {
            const prevPoint = polygonMode.points[polygonMode.points.length - 2];
            const line = new fabric.Line([prevPoint.x, prevPoint.y, point.x, point.y], LINE_OPTIONS);
            canvas.add(line);
        }

        if (polygonMode.drawingLine) canvas.remove(polygonMode.drawingLine);
        polygonMode.drawingLine = new fabric.Line([point.x, point.y, point.x, point.y], TEMP_LINE_OPTIONS);
        canvas.add(polygonMode.drawingLine);

        canvas.requestRenderAll();
        // console.log(`Polygon point added: (${point.x.toFixed(1)}, ${point.y.toFixed(1)}). Total points: ${polygonMode.points.length}`);
    }

    /**
     * Finaliza el dibujo del polígono actual.
     * OBJETIVO: Crear el objeto ROI final y limpiar los elementos de ayuda.
     * CÓMO:
     *   1. Verifica si hay suficientes puntos (>= 3). Si no, cancela y limpia (`_cleanupPolygonDrawing`).
     *   2. Crea un objeto `fabric.Polygon` usando los `polygonMode.points` acumulados.
     *   3. Aplica los estilos `ROI_OPTIONS` (importante: incluye `isRoi: true`).
     *   4. Añade el polígono final al canvas.
     *   5. Llama a `_cleanupPolygonDrawing` para eliminar todos los elementos visuales temporales (círculos, líneas).
     *   6. Guarda el estado en el historial (`_saveHistoryState`).
     *   7. Cambia automáticamente a la herramienta 'select' para facilitar la manipulación posterior.
     */
    function _finishPolygon() {
        if (polygonMode.points.length < 3) {
            console.warn("Need at least 3 points for a polygon. Cancelling.");
            _cleanupPolygonDrawing();
            return;
        }

        const finalPolygon = new fabric.Polygon(polygonMode.points, {
             ...ROI_OPTIONS
        });
        canvas.add(finalPolygon);

        _cleanupPolygonDrawing();
        _saveHistoryState();
        // console.log("Polygon finished and added.");
        setActiveTool('select');
    }

    /**
     * Limpia todos los elementos visuales temporales asociados al dibujo de polígonos.
     * OBJETIVO: Eliminar del canvas los círculos, líneas y la línea temporal usados como guía.
     * CÓMO: Itera sobre todos los objetos del canvas y elimina aquellos marcados con `isHelper: true`.
     *       También elimina la línea temporal (`polygonMode.drawingLine`) si existe.
     *       Resetea el estado `polygonMode` (puntos y línea).
     *       Oculta el tooltip de ayuda si estaba visible.
     * CUÁNDO SE USA: Al finalizar un polígono (`_finishPolygon`), al cancelarlo (`_handleKeyDown` con ESC),
     *                o al cambiar de herramienta si se estaba dibujando un polígono (`setActiveTool`).
     */
    function _cleanupPolygonDrawing() {
        if (!canvas) return;
        canvas.getObjects().forEach(obj => { if (obj.isHelper) canvas.remove(obj); });
        if (polygonMode.drawingLine) canvas.remove(polygonMode.drawingLine);
        polygonMode.points = [];
        polygonMode.drawingLine = null;
        canvas.requestRenderAll();
        const helpTooltip = document.getElementById('polygon-help-roi');
        if(helpTooltip) helpTooltip.style.display = 'none';
    }

    // --- Funciones de Herramientas Adicionales y Teclado ---

    /**
     * Elimina el objeto actualmente seleccionado en el canvas.
     * OBJETIVO: Permitir al usuario borrar ROIs.
     * CÓMO:
     *   1. Obtiene el objeto activo (`canvas.getActiveObject()`).
     *   2. **Verifica si el objeto existe y tiene la propiedad `isRoi: true`.**
     *      POR QUÉ: Solo queremos permitir borrar las ROIs que hemos creado nosotros,
     *              no otros posibles elementos del canvas (como la imagen de fondo, si fuera seleccionable).
     *   3. Si es una ROI válida, la elimina (`canvas.remove`), deselecciona (`canvas.discardActiveObject`),
     *      redibuja y guarda el estado en el historial.
     */
    function _deleteSelectedObject() {
        if (!canvas) return;
        const activeObject = canvas.getActiveObject();
        if (activeObject && activeObject.isRoi) {
            canvas.remove(activeObject);
            canvas.discardActiveObject();
            canvas.requestRenderAll();
            _saveHistoryState();
            // console.log("Selected ROI deleted.");
        } else if (activeObject) {
            // console.log("Selected object is not a valid ROI to delete.");
        } else {
            // console.log("No ROI selected for deletion.");
        }
    }

    /**
     * Manejador global para eventos de teclado (pulsar tecla).
     * OBJETIVO: Implementar atajos de teclado para acciones comunes.
     * CÓMO: Se adjunta al `document` en `initializeRoiEditor`.
     *       Ignora las teclas si el foco está en un campo de entrada de texto/select.
     *       Implementa:
     *         - Borrar (Supr/Backspace): Llama a `_deleteSelectedObject`. Previene la acción por defecto del navegador.
     *         - Deshacer (Ctrl+Z / Cmd+Z): Llama a `_undoLastAction`. Previene la acción por defecto.
     *         - Rehacer (Ctrl+Y / Cmd+Y): Llama a `_redoNextAction`. Previene la acción por defecto.
     *         - Cancelar Polígono (ESC): Si se está dibujando un polígono, llama a `_cleanupPolygonDrawing`.
     *         - (Opcional) Cambiar Herramienta (S, P, F): Comentado por defecto.
     */
    function _handleKeyDown(e) {
         const activeElement = document.activeElement.tagName;
         const typingInInput = (activeElement === 'INPUT' || activeElement === 'TEXTAREA' || activeElement === 'SELECT');

        if ((e.key === 'Delete' || e.key === 'Backspace') && canvas && !typingInInput) {
             e.preventDefault();
             _deleteSelectedObject();
        }

        if ((e.ctrlKey || e.metaKey) && !typingInInput) {
            if (e.key === 'z') {
                e.preventDefault();
                _undoLastAction();
            } else if (e.key === 'y') {
                e.preventDefault();
                _redoNextAction();
            }
        }

        if (e.key === 'Escape' && polygonMode.active && currentTool === 'polygon' && polygonMode.points.length > 0) {
             e.preventDefault();
             // console.log("ESC detected during polygon drawing. Cancelling.");
             _cleanupPolygonDrawing();
        }
    }

    // --- Funciones de Historial Undo/Redo ---
    function _saveHistoryState() {
        if (!canvas) return;
        const jsonState = canvas.toDatalessJSON(['isRoi', 'isHelper']);
        if (currentStateIndex < historyStack.length - 1) {
            historyStack = historyStack.slice(0, currentStateIndex + 1);
        }
        historyStack.push(jsonState);
        currentStateIndex = historyStack.length - 1;
        // console.log(`History saved. Index: ${currentStateIndex}, Total states: ${historyStack.length}`);
        _updateUndoRedoButtons();
    }

    function _loadHistoryState(stateIndex) {
        if (!canvas || stateIndex < 0 || stateIndex >= historyStack.length) return;

        const jsonState = historyStack[stateIndex];
        currentStateIndex = stateIndex;

        canvas.loadFromJSON(jsonState, () => {
            canvas.renderAll();
            // console.log(`History loaded. Index: ${currentStateIndex}`);

            canvas.getObjects().forEach(obj => {
                 if(obj.isHelper) { obj.selectable = false; obj.evented = false; }
            });
            canvas.renderAll();

            _updateUndoRedoButtons();
        });
    }

    function _undoLastAction() {
        if (currentStateIndex > 0) {
            _loadHistoryState(currentStateIndex - 1);
        } else {
            // console.log("No more actions to undo.");
        }
    }

    function _redoNextAction() {
        if (currentStateIndex < historyStack.length - 1) {
            _loadHistoryState(currentStateIndex + 1);
        } else {
            // console.log("No more actions to redo.");
        }
    }

    function _resetHistory() {
        historyStack = [];
        currentStateIndex = -1;
        _updateUndoRedoButtons();
    }

    function _updateUndoRedoButtons() {
        const undoBtn = document.getElementById('tool-undo');
        const redoBtn = document.getElementById('tool-redo');
        if (undoBtn) undoBtn.disabled = currentStateIndex <= 0;
        if (redoBtn) redoBtn.disabled = currentStateIndex >= historyStack.length - 1;
    }

     // --- Funciones de Limpieza y Obtención de Datos ---
     function _clearAllROIs(saveHistory = true) {
         if (!canvas) return;
         let removed = false;
         const objectsToRemove = canvas.getObjects().filter(obj => obj.isRoi);
         objectsToRemove.forEach(obj => {
             canvas.remove(obj);
             removed = true;
         });

         if (removed) {
              canvas.renderAll();
              if (saveHistory) _saveHistoryState();
              // console.log("All ROIs cleared.");
         }
     }

    // --- Funciones Públicas del Módulo (Interfaz del Editor) ---
    function initializeRoiEditor(imageUrl) {
         if (canvas) {
             document.removeEventListener('keydown', _handleKeyDown);
             canvas.dispose();
             canvas = null;
             // console.log("Previous canvas disposed.");
         }

         const canvasElement = document.getElementById('roi-canvas');
         const wrapperElement = document.getElementById('canvas-wrapper');
         if (!canvasElement || !wrapperElement) {
             console.error("Canvas elements not found!");
             return;
         }

         canvasElement.width = wrapperElement.clientWidth;
         canvasElement.height = wrapperElement.clientHeight;

         canvas = new fabric.Canvas('roi-canvas', {
            selection: true,
         });
         // console.log(`Canvas initialized: ${canvas.width}x${canvas.height}`);

         fabric.Image.fromURL(imageUrl, function(img) {
             // console.log(`Fabric: Image loaded ok. Original dims: ${img.width}x${img.height}`);
             const maxWidth = canvas.width;
             const maxHeight = canvas.height;
             let scale = 1;
             if (img.width > 0 && img.height > 0) {
                scale = Math.min(maxWidth / img.width, maxHeight / img.height, 1);
             } else {
                console.error("Image has invalid dimensions (width or height is 0).");
                scale = 1;
             }

             if (!isFinite(scale) || scale <= 0) {
                 console.error("Invalid scale calculated. Using 1.", {maxWidth, maxHeight, imgW: img.width, imgH: img.height});
                 scale = 1;
             }
             // console.log(`Fabric: Calculated scale: ${scale}`);

             canvas.setBackgroundImage(img, () => {
                 canvas.renderAll();
                 // console.log("Fabric: Background image set and rendered.");

                 const upperCanvasEl = canvas.getSelectionElement();
                 if (upperCanvasEl) {
                      upperCanvasEl.style.pointerEvents = 'auto';
                      // console.log("Fabric: Set pointer-events: auto on upper-canvas.");
                 } else {
                      console.warn("Fabric: Could not find upper-canvas element.");
                 }

                 canvas.off('mouse:down');
                 canvas.off('mouse:move');
                 canvas.off('mouse:dblclick');
                 canvas.off('path:created');
                 canvas.on('mouse:down', _handleRoiMouseDown);
                 canvas.on('mouse:move', _handleRoiMouseMove);
                 canvas.on('mouse:dblclick', _handleRoiDoubleClick);
                 canvas.on('path:created', _handlePathCreated);
                 // console.log("Fabric: Canvas event listeners attached.");

                 _clearAllROIs(false);
                 _resetHistory();
                 _saveHistoryState();
                 setActiveTool('select');

             }, {
                 scaleX: scale, scaleY: scale,
                 top: (maxHeight - img.height * scale) / 2,
                 left: (maxWidth - img.width * scale) / 2,
                 originX: 'left', originY: 'top',
                 selectable: false, evented: false
             });

         }, {
             crossOrigin: 'anonymous',
             onError: (error) => {
                 console.error("Error loading image with Fabric.js:", error);
                 alert("Error loading image into editor. Please check the console.");
                 if (window.navigateStep) window.navigateStep('step-upload');
             }
         });

         document.removeEventListener('keydown', _handleKeyDown);
         document.addEventListener('keydown', _handleKeyDown);
         // console.log("Document keydown listener attached.");

         const brushSizeSlider = document.getElementById('brush-size');
         const brushSizeValue = document.getElementById('brush-size-value');
         if (brushSizeSlider && brushSizeValue) {
             const newSlider = brushSizeSlider.cloneNode(true);
             brushSizeSlider.parentNode.replaceChild(newSlider, brushSizeSlider);
             newSlider.addEventListener('input', (e) => {
                 const size = e.target.value;
                 if (freehandMode.active && canvas?.freeDrawingBrush) {
                     canvas.freeDrawingBrush.width = parseInt(size, 10);
                 }
                 brushSizeValue.textContent = size;
             });
             brushSizeValue.textContent = newSlider.value;
         }
     }

     function setActiveTool(toolName) {
         currentTool = toolName;
         // console.log("Switching to tool:", toolName);
         if (!canvas) {
             console.error("Set tool called but canvas is not initialized.");
             return;
         }

         polygonMode.active = false;
         canvas.isDrawingMode = false;
         freehandMode.active = false;
         canvas.selection = false;
         canvas.defaultCursor = 'default';
         canvas.hoverCursor = 'default';
         canvas.discardActiveObject();
         canvas.requestRenderAll();

         const freehandOptions = document.getElementById('freehand-options');
         const polygonHelp = document.getElementById('polygon-help-roi');
         if (freehandOptions) freehandOptions.style.display = 'none';
         if (polygonHelp) polygonHelp.style.display = 'none';

         if (toolName !== 'polygon') {
            _cleanupPolygonDrawing();
         }

         switch (toolName) {
             case 'select':
                 canvas.selection = true;
                 canvas.defaultCursor = 'default';
                 canvas.hoverCursor = 'move';
                 break;
             case 'polygon':
                 polygonMode.active = true;
                 polygonMode.points = [];
                 canvas.defaultCursor = 'crosshair';
                 canvas.hoverCursor = 'crosshair';
                 if (polygonHelp) polygonHelp.style.display = 'block';
                 break;
             case 'freehand':
                 canvas.isDrawingMode = true;
                 freehandMode.active = true;
                 if (!canvas.freeDrawingBrush) {
                     canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
                 }
                 canvas.freeDrawingBrush.color = FREEHAND_ROI_OPTIONS.stroke;
                 canvas.freeDrawingBrush.width = parseInt(document.getElementById('brush-size')?.value || 3, 10);
                 if (freehandOptions) freehandOptions.style.display = 'block';
                 break;
             case 'delete':
                  _deleteSelectedObject();
                  setActiveTool('select');
                  return;
             case 'undo':
                  _undoLastAction();
                  setActiveTool('select');
                  return;
             case 'redo':
                  _redoNextAction();
                  setActiveTool('select');
                  return;
         }

         document.querySelectorAll('.roi-toolbar .tool-button').forEach(btn => {
             btn.classList.remove('active');
             if (btn.id === `tool-${currentTool}`) {
                 btn.classList.add('active');
             }
         });
     }

     function getRoiDataForBackend() {
         if (!canvas || !canvas.backgroundImage) {
              console.error("Canvas or background image not ready for ROI extraction.");
              return [];
         }

         const rois = [];
         const background = canvas.backgroundImage;
         const offsetX = background.left || 0;
         const offsetY = background.top || 0;

         // New way: Use direct ratio of original size to displayed size
         const displayedWidth = background.width * (background.scaleX || 1);
         const displayedHeight = background.height * (background.scaleY || 1);
         // Get original dimensions directly from the image object Fabric loaded
         // Note: background.getElement() gives the underlying HTMLImageElement
         const originalWidth = background.getElement()?.naturalWidth || background.width; // Fallback to background.width if needed
         const originalHeight = background.getElement()?.naturalHeight || background.height; // Fallback to background.height if needed

         // Prevent division by zero if displayed dimensions are somehow zero
         const widthRatio = (displayedWidth > 0) ? originalWidth / displayedWidth : 1;
         const heightRatio = (displayedHeight > 0) ? originalHeight / displayedHeight : 1;

         console.log('[DEBUG] Extracting ROIs. Background props:', {
             offsetX, offsetY,
             displayedWidth, displayedHeight,
             originalWidth, originalHeight,
             widthRatio, heightRatio
          });

         canvas.getObjects().forEach((obj, index) => {
             if (obj.isRoi) {
                 let points = [];
                 const transformMatrix = obj.calcTransformMatrix();

                 // Get points in absolute canvas coordinates (same as before)
                 if (obj.type === 'polygon' && obj.points) {
                     points = obj.points.map(p => fabric.util.transformPoint({ x: p.x, y: p.y }, transformMatrix));
                 } else if (obj.type === 'path' && obj.path) {
                     points = obj.path.reduce((acc, segment) => {
                         const command = segment[0].toUpperCase();
                         const p = { x: segment[segment.length - 2], y: segment[segment.length - 1] };
                         acc.push(fabric.util.transformPoint(p, transformMatrix));
                         return acc;
                     }, []);
                 } else {
                      console.warn(`[ROI ${index}] Unsupported ROI object type for export:`, obj.type);
                      return;
                 }

                 // Apply the refined transformation
                 const originalImagePoints = points.map(p => [
                     Math.round((p.x - offsetX) * widthRatio),
                     Math.round((p.y - offsetY) * heightRatio)
                 ]);

                 console.log(`[DEBUG] ROI ${rois.length + 1} (${obj.type}): Canvas points (transformed)=`, points.length, `Original points=`, originalImagePoints.length);

                 if (originalImagePoints.length >= 3) {
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
     }

    function setupToolbarListeners() {
         // console.log("Setting up ROI toolbar listeners...");
         document.getElementById('tool-select')?.addEventListener('click', () => setActiveTool('select'));
         document.getElementById('tool-polygon')?.addEventListener('click', () => setActiveTool('polygon'));
         document.getElementById('tool-freehand')?.addEventListener('click', () => setActiveTool('freehand'));
         document.getElementById('tool-delete')?.addEventListener('click', () => setActiveTool('delete'));
         document.getElementById('tool-undo')?.addEventListener('click', () => setActiveTool('undo'));
         document.getElementById('tool-redo')?.addEventListener('click', () => setActiveTool('redo'));
         _updateUndoRedoButtons();
    }

    return {
        initialize: initializeRoiEditor,
        getRoiData: getRoiDataForBackend,
        setupToolbar: setupToolbarListeners
    };

})();

document.addEventListener('DOMContentLoaded', () => {
     // console.log("DOM fully loaded and parsed.");

     RoiEditor.setupToolbar();

     const AppState = {
         currentStepId: 'step-upload',
         selectedFile: null,
         imageDataUrl: null
     };

     const form = document.getElementById('diagnosis-form');
     const uploadZone = document.getElementById('upload-zone');
     const imageInput = document.getElementById('image');
     const fileNameDisplay = document.getElementById('file-name-display');
     const startAnalysisButton = document.getElementById('start-analysis-button');
     const imagePreviewContainer = document.getElementById('image-preview-container');
     const globalErrorDiv = document.getElementById('global-error-message');
     const confirmRoisButton = document.getElementById('confirm-rois-button');
     const roiDataInput = document.getElementById('roi_data');

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

     window.navigateStep = function(targetStepId) {
         clearGlobalError();
         // console.log(`Navigating to step: ${targetStepId}`);
         AppState.currentStepId = targetStepId;

         document.querySelectorAll('.step-content').forEach(step => step.classList.remove('active'));
         const targetStepElement = document.getElementById(targetStepId);

         if (targetStepElement) {
             targetStepElement.classList.add('active');
             updateProgressBar(targetStepId);
             targetStepElement.scrollIntoView({ behavior: 'smooth', block: 'start' });

             if (targetStepId === 'step-roi-editor' && AppState.imageDataUrl) {
                 requestAnimationFrame(() => {
                     // console.log("Calling RoiEditor.initialize with image URL...");
                     RoiEditor.initialize(AppState.imageDataUrl);
                 });
             }
             else if (targetStepId === 'step-results') {
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

     if (uploadZone && imageInput && startAnalysisButton && fileNameDisplay && imagePreviewContainer) {

         imageInput.addEventListener('change', handleFileSelect);

         ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
             uploadZone.addEventListener(eventName, preventDefaults, false);
             document.body.addEventListener(eventName, preventDefaults, false);
         });
         ['dragenter', 'dragover'].forEach(eventName => {
             uploadZone.addEventListener(eventName, () => uploadZone.classList.add('dragover'), false);
         });
         ['dragleave', 'drop'].forEach(eventName => {
             uploadZone.addEventListener(eventName, () => uploadZone.classList.remove('dragover'), false);
         });
         uploadZone.addEventListener('drop', handleFileDrop, false);

         startAnalysisButton.addEventListener('click', () => {
             clearGlobalError();
             const fileToProcess = AppState.selectedFile;

             if (fileToProcess) {
                 console.log("Start Analysis button clicked. File:", fileToProcess.name);
                 if (AppState.imageDataUrl) {
                     navigateStep('step-loading');
                     setTimeout(() => {
                         console.log("Image data loaded. Navigating to step-roi-editor...");
                         navigateStep('step-roi-editor');
                     }, 500);
                 } else {
                     console.error("AppState.imageDataUrl is null when trying to start analysis.");
                     showGlobalError("Error procesando la previsualización. Intenta seleccionar la imagen de nuevo.");
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

     function preventDefaults(e) {
         e.preventDefault();
         e.stopPropagation();
     }

     function handleFileSelect(event) {
         clearGlobalError();
         const file = event.target.files[0];
         imageInput.files = event.target.files;
         displayFileNameAndEnableButton(file);
     }

     function handleFileDrop(e) {
         clearGlobalError();
         const dt = e.dataTransfer;
         const file = dt.files[0];
         imageInput.files = dt.files;
         displayFileNameAndEnableButton(file);
     }

     function displayFileNameAndEnableButton(file) {
         clearGlobalError();
         if (file && file.type.startsWith('image/')) {
             fileNameDisplay.textContent = `Archivo: ${file.name}`;
             startAnalysisButton.disabled = false;
             AppState.selectedFile = file;

             if (imagePreviewContainer) {
                 imagePreviewContainer.innerHTML = '';
                 const img = document.createElement('img');
                 img.style.maxWidth = '100px';
                 img.style.maxHeight = '70px';
                 img.style.borderRadius = '4px';
                 img.style.objectFit = 'cover';

                 const reader = new FileReader();
                 reader.onload = function(e) {
                     img.src = e.target.result;
                     AppState.imageDataUrl = e.target.result;
                     console.log("FileReader success: Image preview ready, DataURL stored.");
                 }
                 reader.onerror = function(e) {
                     console.error("FileReader error:", e);
                     showGlobalError("Error leyendo la previsualización de la imagen.");
                     AppState.imageDataUrl = null;
                     startAnalysisButton.disabled = true;
                 }
                 reader.readAsDataURL(file);

                 imagePreviewContainer.appendChild(img);
                 imagePreviewContainer.style.display = 'block';
             } else {
                 console.warn("Image preview container not found. DataURL not generated on file select.");
                 AppState.imageDataUrl = null;
             }

         } else {
             fileNameDisplay.textContent = file ? `Formato no soportado: ${file.name}` : "";
             startAnalysisButton.disabled = true;
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

     if (confirmRoisButton && roiDataInput) {
         confirmRoisButton.addEventListener('click', () => {
             clearGlobalError();
             const roiDataArray = RoiEditor.getRoiData();

             if (roiDataArray.length === 0) {
                 const proceed = confirm("Advertencia: No has dibujado ninguna Región de Interés (ROI). La puntuación digital será 0. ¿Deseas continuar?");
                 if (!proceed) return;
             }

             try {
                 roiDataInput.value = JSON.stringify(roiDataArray);
                 // console.log("ROI data set in hidden input:", roiDataInput.value);
                 navigateStep('step-manual-data');
                 setTimeout(() => openTab(null, 'tab-clinical'), 0);
             } catch (e) {
                 console.error("Error stringifying ROI data:", e);
                 showGlobalError("Error interno al procesar las ROIs. Inténtalo de nuevo.");
             }
         });
     } else {
        console.error("Confirm ROIs button or hidden input not found.");
     }

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
         const clickedButton = evt ? evt.currentTarget : Array.from(tablinks).find(btn => btn.getAttribute('onclick')?.includes(`'${tabName}'`));
         if (clickedButton) clickedButton.classList.add('active');
     }

     document.querySelectorAll('select.score-select').forEach(select => {
         select.addEventListener('change', function() {
             const selectedOption = this.options[this.selectedIndex];
             const score = parseInt(selectedOption.value, 10);
             this.className = 'score-select';
             if (!isNaN(score)) {
                  let scoreClass = 'score-unknown';
                  if (score === 0) scoreClass = 'score-0';
                  else if (score === 1 || score === 2) scoreClass = 'score-1-2';
                  else if (score === 3) scoreClass = 'score-3';
                  else if (score >= 4) scoreClass = 'score-4-plus';
                  this.classList.add(scoreClass);
             }
         });
         select.dispatchEvent(new Event('change'));
     });

    const resultsSection = document.getElementById('step-results');
    if (resultsSection && resultsSection.classList.contains('active')) {
        navigateStep('step-results');
    } else {
        navigateStep('step-upload');
    }

    if (document.getElementById('step-manual-data')?.classList.contains('active')) {
        setTimeout(() => openTab(null, 'tab-clinical'), 0);
    }

});