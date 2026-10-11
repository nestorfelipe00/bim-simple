// Proceso principal: ventana, título, menús, diálogos de Windows, pregunta al cerrar y puente con el motor.
// Contratos: specs/001-espacio-trabajo-pisos/contracts/ui.md y programa.md.
const { app, BrowserWindow, Menu, dialog, ipcMain } = require("electron");
const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const { Engine } = require("./engine");
const { validateFile } = require("./validator");

const TEST = process.argv.includes("--test");
const APP_DIR = path.join(__dirname, "..", "..");
const TEST_OUTPUT = path.join(APP_DIR, "test-output");
const APP_ID = "BIMSimple.BIMSimple";

app.setAppUserModelId(APP_ID);
if (TEST) app.setPath("userData", path.join(TEST_OUTPUT, "userdata")); // la prueba no toca %APPDATA%

const pythonExe = app.isPackaged
  ? path.join(process.resourcesPath, "python", "python.exe")
  : path.join(APP_DIR, "..", "runtime", "python", "python.exe");

let win = null;
let engine = null;
let allowClose = false;
let state = { has_project: false, dirty: false, path: "", can_undo: false, can_redo: false };

// ---------- título y menú (FR-003, FR-004) ----------
function windowTitle() {
  if (!state.has_project) return "BIM Simple";
  const name = state.path ? path.basename(state.path) : "Proyecto sin guardar";
  return `${state.dirty ? "* " : ""}${name} — BIM Simple`;
}

function sendMenu(action) {
  return () => win && win.webContents.send("menu", action);
}

function buildMenu() {
  return Menu.buildFromTemplate([
    {
      label: "Archivo",
      submenu: [
        { label: "Nuevo proyecto", accelerator: "CmdOrCtrl+N", click: sendMenu("new") },
        { label: "Abrir IFC…", accelerator: "CmdOrCtrl+O", click: sendMenu("open") },
        { type: "separator" },
        { label: "Guardar IFC", accelerator: "CmdOrCtrl+S", click: sendMenu("save") },
        { label: "Guardar IFC como…", accelerator: "CmdOrCtrl+Shift+S", click: sendMenu("save-as") },
        { type: "separator" },
        { label: "Salir", accelerator: "CmdOrCtrl+Q", click: () => win && win.close() },
      ],
    },
    {
      label: "Edición",
      submenu: [
        { label: "Deshacer", accelerator: "CmdOrCtrl+Z", enabled: !!state.can_undo, click: sendMenu("undo") },
        { label: "Rehacer", accelerator: "CmdOrCtrl+Y", enabled: !!state.can_redo, click: sendMenu("redo") },
      ],
    },
    {
      label: "Ayuda",
      submenu: [{ label: "Acerca de BIM Simple", click: () => showAbout() }],
    },
  ]);
}

function refreshChrome() {
  if (!win) return;
  win.setTitle(windowTitle());
  Menu.setApplicationMenu(buildMenu());
}

// ---------- motor ----------
async function engineRequest(cmd, args = {}) {
  const response = await engine.request(cmd, args);
  const newState = response.ok && (response.result?.state || (cmd === "state" ? response.result : null));
  if (newState) {
    state = newState;
    refreshChrome();
  }
  return response;
}

// ---------- diálogos (en la prueba, una cola de respuestas los reemplaza) ----------
const testLog = { dialogs: [] };
let testAnswers = [];

async function messageBox(options, testDefault) {
  if (TEST) {
    const answer = testAnswers.length ? testAnswers.shift() : testDefault;
    testLog.dialogs.push({ title: options.title, message: options.message, detail: options.detail || "", answer });
    const index = options.buttons.indexOf(answer);
    return index >= 0 ? index : options.cancelId ?? 0;
  }
  const { response } = await dialog.showMessageBox(win, options);
  return response;
}

async function chooseSavePath() {
  if (TEST) {
    const answer = testAnswers.shift();
    testLog.dialogs.push({ title: "Guardar IFC como", answer: answer || "(cancelado)" });
    return answer || null;
  }
  const result = await dialog.showSaveDialog(win, {
    title: "Guardar IFC como",
    defaultPath: state.path || path.join(app.getPath("documents"), "Proyecto.ifc"),
    filters: [{ name: "Modelo IFC", extensions: ["ifc"] }],
  });
  return result.canceled ? null : result.filePath;
}

async function chooseOpenPath() {
  if (TEST) {
    const answer = testAnswers.shift();
    testLog.dialogs.push({ title: "Abrir IFC", answer: answer || "(cancelado)" });
    return answer || null;
  }
  const result = await dialog.showOpenDialog(win, {
    title: "Abrir IFC",
    properties: ["openFile"],
    filters: [{ name: "Modelo IFC", extensions: ["ifc"] }],
  });
  return result.canceled ? null : result.filePaths[0];
}

async function saveProject(asNew) {
  let target = asNew ? null : state.path || null;
  if (!target) {
    target = await chooseSavePath();
    if (!target) return null;
  }
  const response = await engineRequest("save_project", { path: target });
  if (response.ok) {
    validateFile(pythonExe, engineLogFile(), target).then((result) => {
      const text =
        result.errors === null
          ? `Guardado. No se pudo validar: ${result.error}`
          : `Guardado. Validación IFC4: ${result.errors} errores.`;
      testLog.lastValidation = result;
      if (win && !win.isDestroyed()) win.webContents.send("notice", text);
    });
  }
  return response;
}

// Devuelve true si se puede seguir (Nuevo, Abrir, cerrar): no había cambios, se guardaron o el usuario no quiso.
async function askSaveChanges() {
  if (!state.dirty) return true;
  const answer = await messageBox(
    {
      type: "question",
      title: "BIM Simple",
      message: "¿Guardar cambios antes de cerrar?",
      detail: "Si no los guardas, se perderán.",
      buttons: ["Guardar", "No guardar", "Cancelar"],
      defaultId: 0,
      cancelId: 2,
    },
    "No guardar"
  );
  if (answer === 2) return false;
  if (answer === 0) {
    const saved = await saveProject(false);
    return !!(saved && saved.ok);
  }
  return true;
}

function aboutText() {
  return [
    `BIM Simple ${app.getVersion()}`,
    "",
    "Usa estas librerías, cada una con su licencia:",
    "• IfcOpenShell 0.9.0 — LGPL-3.0. Código fuente: https://github.com/IfcOpenShell/IfcOpenShell",
    `• Electron ${process.versions.electron}, Three.js 0.186.1 y camera-controls 3.1.2 — MIT`,
    "• Python 3.14.7 — PSF",
    "",
    "Los textos completos de las licencias están en la carpeta «licencias» del programa.",
  ].join("\n");
}

function showAbout() {
  return messageBox(
    { type: "info", title: "Acerca de BIM Simple", message: aboutText(), buttons: ["Cerrar"], defaultId: 0, cancelId: 0 },
    "Cerrar"
  );
}

function engineLogFile() {
  return path.join(app.getPath("userData"), "logs", "engine.log");
}

// ---------- ventana ----------
function createWindow() {
  win = new BrowserWindow({
    width: 1400,
    height: 860,
    show: !TEST,
    title: "BIM Simple",
    icon: path.join(APP_DIR, "build", "icon.ico"),
    backgroundColor: "#f4f4f2",
    webPreferences: {
      preload: path.join(__dirname, "..", "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      backgroundThrottling: !TEST,
    },
  });
  win.on("page-title-updated", (event) => event.preventDefault()); // el título lo decide BIM Simple
  win.on("close", async (event) => {
    if (allowClose || !state.dirty) {
      engine.stop();
      return;
    }
    event.preventDefault();
    if (await askSaveChanges()) {
      allowClose = true;
      win.close();
    }
  });
  if (TEST) {
    fs.mkdirSync(TEST_OUTPUT, { recursive: true });
    win.webContents.on("console-message", (details) => {
      const d = details || {};
      fs.appendFileSync(path.join(TEST_OUTPUT, "consola.txt"), `[${d.level}] ${d.message} (${d.sourceId}:${d.lineNumber})\n`);
    });
  }
  win.loadFile(path.join(__dirname, "..", "renderer", "index.html"), { query: TEST ? { test: "1" } : {} });
  refreshChrome();
}

// ---------- puente con la página ----------
ipcMain.handle("engine", (_event, cmd, args) => engineRequest(cmd, args));
ipcMain.handle("engine-ready", () => engine.ready());
ipcMain.handle("save", (_event, asNew) => saveProject(asNew));
ipcMain.handle("ask-save-changes", () => askSaveChanges());
ipcMain.handle("open-ifc-dialog", () => chooseOpenPath());
ipcMain.handle("confirm-delete", async (_event, name, count) => {
  const answer = await messageBox(
    {
      type: "warning",
      title: "BIM Simple",
      message: `El piso «${name}» tiene ${count} ${count === 1 ? "elemento" : "elementos"}. Se borrarán junto con el piso.`,
      buttons: ["Borrar", "Cancelar"],
      defaultId: 1,
      cancelId: 1,
    },
    "Borrar"
  );
  return answer === 0;
});
ipcMain.handle("about", () => showAbout());
ipcMain.handle("quit", () => win && win.close());

// Solo para la prueba del programa.
if (TEST) {
  ipcMain.handle("test-capture", async (_event, name) => {
    const image = await win.webContents.capturePage();
    fs.writeFileSync(path.join(TEST_OUTPUT, `${name}.png`), image.toPNG());
    return image.getSize();
  });
  ipcMain.handle("test-answer-dialogs", (_event, labels) => {
    testAnswers = [...labels];
  });
  ipcMain.handle("test-dialog-log", () => testLog);
  ipcMain.handle("test-window-title", () => win.getTitle());
  ipcMain.handle("test-menu-labels", () =>
    Menu.getApplicationMenu().items.map((item) => ({ label: item.label, items: item.submenu.items.filter((i) => i.type !== "separator").map((i) => i.label) }))
  );
  ipcMain.handle("test-kill-engine", () => engine.killForTest());
  ipcMain.handle("test-output-dir", () => TEST_OUTPUT);
  ipcMain.handle("test-fixtures", () => testFixtures);
  // Termina la prueba. Si se pide, el último paso es cerrar la ventana con cambios: lo registra el proceso principal,
  // porque la página desaparece al cerrarse.
  ipcMain.handle("test-finish", async (_event, result) => {
    if (result.closeWithChanges) {
      const before = testLog.dialogs.length;
      const dirty = state.dirty;
      win.close();
      await new Promise((resolve) => setTimeout(resolve, 800));
      const asked = testLog.dialogs.slice(before).some((d) => d.message === "¿Guardar cambios antes de cerrar?");
      const ok = dirty && asked && win.isDestroyed();
      result.steps.push({ section: "Historia 2", name: "Cerrar con la X con cambios: pregunta y cierra con «No guardar»", ok, detail: { dirty, asked, closed: win.isDestroyed() } });
      if (!ok) result.failures += 1;
    }
    result.dialogs = testLog.dialogs;
    result.summary = result.failures === 0 ? "RESULTADO: TODO OK" : `RESULTADO: ${result.failures} FALLAS`;
    fs.writeFileSync(path.join(TEST_OUTPUT, "resultado.json"), JSON.stringify(result, null, 2));
    console.log(result.summary);
    if (engine) engine.stop();
    setTimeout(() => app.exit(result.failures === 0 ? 0 : 1), 200);
  });
}

// IFC de prueba (engine/tests/make_fixtures.py), generados antes de abrir la ventana.
let testFixtures = null;
function makeTestFixtures() {
  const folder = path.join(TEST_OUTPUT, "fixtures");
  const run = spawnSync(pythonExe, ["-m", "tests.make_fixtures", folder], { cwd: path.join(APP_DIR, "..", "engine"), encoding: "utf8" });
  testFixtures = { folder, ok: run.status === 0, output: `${run.stdout || ""}${run.stderr || ""}`.slice(-2000) };
}

app.whenReady().then(() => {
  if (TEST) makeTestFixtures();
  engine = new Engine({ pythonExe, logFile: engineLogFile() });
  engine.on("crashed", () => {
    state = { has_project: false, dirty: false, path: "", can_undo: false, can_redo: false };
    refreshChrome();
    if (win && !win.isDestroyed())
      win.webContents.send(
        "notice",
        "El motor de BIM Simple se detuvo. Los cambios sin guardar se perdieron; el último archivo guardado no se modificó."
      );
  });
  engine.on("restarted", () => win && !win.isDestroyed() && win.webContents.send("engine-restarted"));
  engine.start().catch((error) => console.error("No se pudo iniciar el motor:", error));
  createWindow();
});

app.on("window-all-closed", () => {
  if (!TEST) app.quit();
});
