// Puente seguro entre la ventana y el proceso principal: la página no tiene acceso a Node.
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("bim", {
  motor: (cmd, args) => ipcRenderer.invoke("motor", cmd, args),
  motorListo: () => ipcRenderer.invoke("motor_listo"),
  guardarComo: () => ipcRenderer.invoke("guardar_como"),
  titulo: (texto) => ipcRenderer.send("titulo", texto),
  alMenu: (fn) => ipcRenderer.on("menu", (_e, accion) => fn(accion)),
  captura: (nombre) => ipcRenderer.invoke("captura", nombre),
  finPrueba: (resultado) => ipcRenderer.invoke("fin_prueba", resultado),
});
