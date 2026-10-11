// Proceso principal del prototipo: ventana, menú en español, cierre con pregunta y puente con el motor.
const { app, BrowserWindow, Menu, dialog, ipcMain } = require("electron");
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const readline = require("readline");

const PRUEBA = process.argv.includes("--prueba");
const BASE = path.join(__dirname, "..");
const SALIDA = path.join(BASE, "salida");
const T_INICIO = Date.now();

app.setName("BIM Simple");
app.setAppUserModelId("BIMSimple.Prototipo");

// ---------- motor (Python + IfcOpenShell) ----------
let motor = null;
let siguienteId = 1;
const pendientes = new Map();
let motorListo;
const motorPreparado = new Promise((resolve) => (motorListo = resolve));
let estado = { proyecto: false, sucio: false };

function iniciarMotor() {
  motor = spawn(path.join(BASE, "python", "python.exe"), ["-u", path.join(BASE, "motor", "motor.py")], {
    windowsHide: true,
    stdio: ["pipe", "pipe", "pipe"],
  });
  readline.createInterface({ input: motor.stdout }).on("line", (linea) => {
    const msg = JSON.parse(linea);
    if (msg.id === 0) return motorListo({ ...msg.result, listo_ms: Date.now() - T_INICIO });
    const p = pendientes.get(msg.id);
    if (!p) return;
    pendientes.delete(msg.id);
    msg.ida_vuelta_ms = Date.now() - p.t0;
    const est = msg.result && (msg.result.estado || (msg.result.pisos ? msg.result : null));
    if (est) estado = est;
    p.resolve(msg);
  });
  motor.stderr.on("data", (d) => fs.appendFileSync(path.join(SALIDA, "motor_stderr.txt"), d));
}

function orden(cmd, args = {}) {
  return new Promise((resolve) => {
    const id = siguienteId++;
    pendientes.set(id, { resolve, t0: Date.now() });
    motor.stdin.write(JSON.stringify({ id, cmd, args }) + "\n");
  });
}

// ---------- ventana ----------
let ventana = null;
let cerrarSinPreguntar = false;
const registroPrueba = { preguntas_al_cerrar: [] };

function preguntarAlCerrar() {
  const opciones = {
    type: "question",
    buttons: ["Guardar", "No guardar", "Cancelar"],
    defaultId: 0,
    cancelId: 2,
    title: "BIM Simple",
    message: "¿Guardar cambios antes de cerrar?",
    detail: "Si no los guardas, se perderán.",
  };
  if (PRUEBA) {
    // En la prueba no se muestra el diálogo: se registra que se habría mostrado y se responde "No guardar".
    registroPrueba.preguntas_al_cerrar.push(opciones.message);
    return 1;
  }
  return dialog.showMessageBoxSync(ventana, opciones);
}

async function guardarComo() {
  const r = await dialog.showSaveDialog(ventana, {
    title: "Guardar IFC como",
    defaultPath: estado.ruta || path.join(app.getPath("documents"), "Proyecto.ifc"),
    filters: [{ name: "Modelo IFC", extensions: ["ifc"] }],
  });
  if (r.canceled) return null;
  return orden("guardar", { ruta: r.filePath });
}

function crearMenu() {
  const enviar = (accion) => () => ventana.webContents.send("menu", accion);
  Menu.setApplicationMenu(
    Menu.buildFromTemplate([
      {
        label: "Archivo",
        submenu: [
          { label: "Nuevo proyecto", accelerator: "Ctrl+N", click: enviar("nuevo") },
          { label: "Guardar IFC", accelerator: "Ctrl+S", click: enviar("guardar") },
          { label: "Guardar IFC como…", accelerator: "Ctrl+Shift+S", click: enviar("guardar_como") },
          { type: "separator" },
          { label: "Salir", accelerator: "Ctrl+Q", click: () => ventana.close() },
        ],
      },
      {
        label: "Edición",
        submenu: [
          { label: "Deshacer", accelerator: "Ctrl+Z", click: enviar("deshacer") },
          { label: "Rehacer", accelerator: "Ctrl+Y", click: enviar("rehacer") },
        ],
      },
    ])
  );
}

function crearVentana() {
  ventana = new BrowserWindow({
    width: 1400,
    height: 860,
    show: !PRUEBA,
    title: "BIM Simple",
    icon: path.join(__dirname, "icono.ico"),
    backgroundColor: "#f4f4f2",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      backgroundThrottling: false, // la prueba corre con la ventana oculta
    },
  });
  ventana.on("page-title-updated", (e) => e.preventDefault()); // el título lo decide BIM Simple, no la página
  ventana.on("close", async (e) => {
    if (cerrarSinPreguntar || !estado.sucio) return;
    e.preventDefault();
    const respuesta = preguntarAlCerrar();
    if (respuesta === 2) return; // Cancelar
    if (respuesta === 0) {
      const r = estado.ruta ? await orden("guardar", { ruta: estado.ruta }) : await guardarComo();
      if (!r || !r.ok) return; // si no se guardó, no se cierra
    }
    cerrarSinPreguntar = true;
    ventana.close();
  });
  ventana.loadFile(path.join(__dirname, "index.html"), { query: PRUEBA ? { prueba: "1", salida: SALIDA } : {} });
}

// ---------- puente con la ventana ----------
ipcMain.handle("motor", (_e, cmd, args) => orden(cmd, args));
ipcMain.handle("guardar_como", () => guardarComo());
ipcMain.handle("motor_listo", () => motorPreparado);
ipcMain.on("titulo", (_e, texto) => ventana && ventana.setTitle(texto));

// La prueba automática: captura la ventana (oculta) y comprueba el cierre con la X.
ipcMain.handle("captura", async (_e, nombre) => {
  const imagen = await ventana.webContents.capturePage();
  fs.writeFileSync(path.join(SALIDA, `${nombre}.png`), imagen.toPNG());
  return imagen.getSize();
});
ipcMain.handle("fin_prueba", async (_e, resultado) => {
  const sucioAntes = estado.sucio;
  resultado.titulo_ventana = ventana.getTitle();
  resultado.memoria_mb = Math.round(process.memoryUsage().rss / 1048576);
  ventana.close(); // con cambios sin guardar: debe preguntar y no cerrar todavía
  await new Promise((r) => setTimeout(r, 300));
  resultado.cierre = {
    habia_cambios: sucioAntes,
    pregunto: registroPrueba.preguntas_al_cerrar,
    ventana_cerrada: ventana.isDestroyed(),
  };
  resultado.arranque_hasta_ventana_lista_ms = resultado.listo_en_ms;
  fs.writeFileSync(path.join(SALIDA, "resultado.json"), JSON.stringify(resultado, null, 2));
  console.log(JSON.stringify(resultado, null, 2));
  app.exit(0);
});

app.whenReady().then(() => {
  fs.mkdirSync(SALIDA, { recursive: true });
  iniciarMotor();
  crearMenu();
  crearVentana();
});
app.on("window-all-closed", () => {
  if (!PRUEBA) app.quit(); // en la prueba, el que termina es fin_prueba, después de escribir el resultado
});
app.on("quit", () => motor && motor.kill());
