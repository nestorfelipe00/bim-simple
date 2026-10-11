// Puente seguro entre la página y el proceso principal (contextBridge). La página no tiene acceso a Node.
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("bim", {
  // órdenes al motor
  engine: (cmd, args) => ipcRenderer.invoke("engine", cmd, args),
  engineReady: () => ipcRenderer.invoke("engine-ready"),
  // diálogos y acciones que necesitan al proceso principal
  save: (asNew) => ipcRenderer.invoke("save", asNew),
  askSaveChanges: () => ipcRenderer.invoke("ask-save-changes"),
  openIfc: () => ipcRenderer.invoke("open-ifc-dialog"),
  confirmDelete: (name, count) => ipcRenderer.invoke("confirm-delete", name, count),
  about: () => ipcRenderer.invoke("about"),
  quit: () => ipcRenderer.invoke("quit"),
  // avisos del proceso principal
  onMenu: (fn) => ipcRenderer.on("menu", (_event, action) => fn(action)),
  onNotice: (fn) => ipcRenderer.on("notice", (_event, text) => fn(text)),
  onEngineRestarted: (fn) => ipcRenderer.on("engine-restarted", () => fn()),
  // solo para la prueba del programa
  test: {
    capture: (name) => ipcRenderer.invoke("test-capture", name),
    answerDialogs: (labels) => ipcRenderer.invoke("test-answer-dialogs", labels),
    dialogLog: () => ipcRenderer.invoke("test-dialog-log"),
    windowTitle: () => ipcRenderer.invoke("test-window-title"),
    menuLabels: () => ipcRenderer.invoke("test-menu-labels"),
    killEngine: () => ipcRenderer.invoke("test-kill-engine"),
    finish: (result) => ipcRenderer.invoke("test-finish", result),
  },
});
