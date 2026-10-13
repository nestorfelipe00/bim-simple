// Controlador de la página: un solo punto que manda las órdenes al motor, reemplaza el estado con cada
// respuesta y actualiza el panel y las vistas (plan.md, "Interfaz").
// Función 002: caja de herramientas, Info Box y herramienta Muro (specs/002-muros-capas/contracts/ui.md).
import { Viewports } from "./viewports.js";
import { MeshStore } from "./meshes.js";
import { StoreyPanel } from "./storey-panel.js";
import { Toolbox } from "./toolbox.js";
import { InfoBox } from "./infobox.js";
import { WallTool } from "./wall-tool.js";
import { StructuresDialog } from "./structures-dialog.js";
import { Selection } from "./selection.js";

const $ = (id) => document.getElementById(id);
const REFRESH_ALL = new Set(["new_project", "open_project", "undo", "redo"]);

const viewports = new Viewports({
  canvas: $("canvas"),
  planDiv: $("plan-view"),
  view3dDiv: $("view-3d"),
  planLabel: $("plan-label"),
});
const meshes = new MeshStore(viewports);
let state = { has_project: false, has_building: false, storeys: [], active_storey_id: null, materials: [], structures: [] };
let tool = "arrow";
let lastContext = ""; // proyecto y piso activo: si cambian, la cadena de muros termina
const panel = new StoreyPanel({ onAction: (action, arg) => handleAction(action, arg) });
const toolbox = new Toolbox({ onChange: (name) => setTool(name) });
const infobox = new InfoBox({
  onEdit: () => null, // cambios de la selección: Historia 4
  onSplit: () => splitSelected(),
  onDelete: () => null, // borrar: Historia 4
  onOpenStructures: () => handleAction("structures"),
  showMessage,
});
const selection = new Selection({
  viewports,
  meshes,
  onChange: () => infobox.render(state, { tool, selection: selection.walls() }),
});
const structuresDialog = new StructuresDialog();
const wallTool = new WallTool({
  viewports,
  meshes,
  infobox,
  getState: () => state,
  onCreate: (start, end) => dispatch("create_wall", { start, end, ...infobox.toolValues() }),
  showMessage,
});

function showMessage(text, isError = false) {
  const box = $("messages");
  box.textContent = text || "";
  box.classList.toggle("error", !!isError);
}

function setTool(name) {
  if (name === tool) return;
  wallTool.cancel();
  tool = name;
  toolbox.set(name);
  if (name === "wall") selection.clear(); // elegir Muro deja la selección vacía (ui.md)
  infobox.render(state, { tool, selection: selection.walls() });
}

// Separar en capas (FR-019 a FR-022): la selección pasa a las capas nuevas.
async function splitSelected() {
  const response = await dispatch("split_walls", { ids: selection.ids });
  if (response.ok) selection.set(response.result.new_ids);
  return response;
}

function render() {
  meshes.setMaterials(state.materials);
  panel.render(state);
  const active = state.storeys.find((s) => s.id === state.active_storey_id);
  viewports.setActiveStorey(state.active_storey_id, active ? active.name : "", active ? active.elevation : 0);
  const context = `${state.has_project}|${state.path}|${state.active_storey_id}`;
  if (context !== lastContext) wallTool.cancel(); // FR-010 y casos límite: cambiar de piso o de proyecto
  lastContext = context;
  toolbox.enable(state.has_project);
  selection.keepExisting();
  infobox.render(state, { tool, selection: selection.walls() });
}

async function dispatch(cmd, args = {}) {
  const started = performance.now();
  const response = await bim.engine(cmd, args);
  if (!response.ok) {
    showMessage(response.error, true);
    response.total_ms = Math.round(performance.now() - started);
    return response;
  }
  const result = response.result;
  if (result.state) state = result.state;
  else if (cmd === "state") state = result;
  const hadMeshes = meshes.size > 0;
  if (cmd === "new_project" || cmd === "open_project") setTool("arrow"); // FR-001
  if (REFRESH_ALL.has(cmd)) {
    meshes.clear();
    if (state.has_project) {
      const all = await bim.engine("meshes", {});
      if (all.ok) meshes.apply(all.result);
    }
  } else {
    for (const id of result.deleted_ids || []) meshes.remove(id);
    if (result.changed_ids && result.changed_ids.length) {
      const changed = await bim.engine("meshes", { ids: result.changed_ids });
      if (changed.ok) meshes.apply(changed.result);
    }
  }
  render();
  if (meshes.size > 0 && (!hadMeshes || cmd === "open_project") && cmd !== "create_wall") viewports.fit({ animate: false });
  showMessage("");
  response.total_ms = Math.round(performance.now() - started);
  return response;
}

async function handleAction(action, arg) {
  const selected = panel.selected();
  switch (action) {
    case "new":
      if (await bim.askSaveChanges()) return dispatch("new_project");
      return null;
    case "open": {
      if (!(await bim.askSaveChanges())) return null;
      const path = await bim.openIfc();
      return path ? dispatch("open_project", { path }) : null;
    }
    case "save":
    case "save-as": {
      const response = await bim.save(action === "save-as");
      if (response && !response.ok) showMessage(response.error, true);
      if (response && response.ok) {
        state = response.result.state;
        render();
        showMessage("Guardado. Validando el archivo…");
      }
      return response;
    }
    case "undo":
      return dispatch("undo");
    case "redo":
      return dispatch("redo");
    case "add-above":
      return dispatch("add_storey_above");
    case "add-below":
      return dispatch("add_storey_below");
    case "edit": {
      if (!selected) return null;
      const changes = await panel.editDialog(selected);
      if (!changes || Object.keys(changes).length === 0) return null;
      return dispatch("edit_storey", { id: selected.id, ...changes });
    }
    case "delete": {
      if (!selected) return null;
      if (selected.elements > 0 && !(await bim.confirmDelete(selected.name, selected.elements))) return null;
      return dispatch("delete_storey", { id: selected.id });
    }
    case "activate":
      return dispatch("activate_storey", { id: arg });
    case "fit":
      viewports.fit();
      return null;
    case "structures": // Opciones > Estructuras compuestas… y el botón "…" del Info Box (FR-015)
      if (!state.has_project) return null;
      wallTool.cancel();
      return structuresDialog.open(state, (payload) => dispatch("apply_structures", payload));
    default:
      return null;
  }
}

// ---------- ratón y teclado en la planta (función 002) ----------
// La prueba del programa llama a estas mismas funciones con eventos armados (app/test/window-test.js).
function planPointer(type, event) {
  if (!state.has_project) return null;
  if (type === "contextmenu") {
    if (tool === "wall") wallTool.cancel();
    return null;
  }
  if (tool === "wall") return type === "move" ? wallTool.pointerMove(event) : wallTool.pointerDown(event);
  if (type === "down" && event.button === 0) return selection.clickPlan(event); // Flecha (FR-023)
  return null;
}

viewports.on3dClick = (event, hit) => {
  if (state.has_project && tool === "arrow") selection.click3d(event, hit);
};

async function keyDown(event) {
  const target = event.target || {};
  if (["INPUT", "SELECT", "TEXTAREA"].includes(target.tagName) || document.querySelector("dialog[open]")) return false;
  if (!state.has_project) return false;
  if (tool === "wall") {
    const handled = await wallTool.key(event);
    if (handled && event.preventDefault) event.preventDefault();
    return handled;
  }
  if (event.key === "Escape") {
    selection.clear();
    return true;
  }
  return false;
}

const planDiv = $("plan-view");
planDiv.addEventListener("pointermove", (event) => planPointer("move", event));
planDiv.addEventListener("pointerdown", (event) => {
  if (event.button === 0 || event.button === 2) planPointer("down", event);
});
planDiv.addEventListener("contextmenu", (event) => {
  event.preventDefault();
  planPointer("contextmenu", event);
});
window.addEventListener("keydown", (event) => keyDown(event));

bim.onMenu((action) => handleAction(action));
bim.onNotice((text) => showMessage(text, text.startsWith("El motor")));
bim.onEngineRestarted(() => {
  state = { has_project: false, has_building: false, storeys: [], active_storey_id: null, materials: [], structures: [] };
  meshes.clear();
  wallTool.cancel();
  render();
});

const ready = await bim.engineReady();
await dispatch("state");
showMessage("Listo.");

// Para la prueba del programa (ventana oculta, ?test=1).
if (new URLSearchParams(location.search).get("test") === "1") {
  const { run } = await import("../../test/window-test.js");
  run({
    ready, getState: () => state, dispatch, handleAction, panel, viewports, meshes, showMessage,
    toolbox, infobox, wallTool, setTool, getTool: () => tool, planPointer, keyDown, structuresDialog, selection,
  });
}
