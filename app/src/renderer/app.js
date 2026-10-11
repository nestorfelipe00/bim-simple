// Controlador de la página: un solo punto que manda las órdenes al motor, reemplaza el estado con cada
// respuesta y actualiza el panel y las vistas (plan.md, "Interfaz").
import { Viewports } from "./viewports.js";
import { MeshStore } from "./meshes.js";
import { StoreyPanel } from "./storey-panel.js";

const $ = (id) => document.getElementById(id);
const REFRESH_ALL = new Set(["new_project", "open_project", "undo", "redo"]);

const viewports = new Viewports({
  canvas: $("canvas"),
  planDiv: $("plan-view"),
  view3dDiv: $("view-3d"),
  planLabel: $("plan-label"),
});
const meshes = new MeshStore(viewports);
let state = { has_project: false, has_building: false, storeys: [], active_storey_id: null };
const panel = new StoreyPanel({ onAction: (action, arg) => handleAction(action, arg) });

function showMessage(text, isError = false) {
  const box = $("messages");
  box.textContent = text || "";
  box.classList.toggle("error", !!isError);
}

function render() {
  panel.render(state);
  const active = state.storeys.find((s) => s.id === state.active_storey_id);
  viewports.setActiveStorey(state.active_storey_id, active ? active.name : "");
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
  if (meshes.size > 0 && (!hadMeshes || cmd === "open_project")) viewports.fit({ animate: false });
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
    default:
      return null;
  }
}

bim.onMenu((action) => handleAction(action));
bim.onNotice((text) => showMessage(text, text.startsWith("El motor")));
bim.onEngineRestarted(() => {
  state = { has_project: false, has_building: false, storeys: [], active_storey_id: null };
  meshes.clear();
  render();
});

const ready = await bim.engineReady();
await dispatch("state");
showMessage("Listo.");

// Para la prueba del programa (ventana oculta, ?test=1).
if (new URLSearchParams(location.search).get("test") === "1") {
  const { run } = await import("../../test/window-test.js");
  run({ ready, getState: () => state, dispatch, handleAction, panel, viewports, meshes, showMessage });
}
