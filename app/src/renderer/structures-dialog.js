// Diálogo "Estructuras compuestas" (función 002; FR-015, FR-016; contracts/ui.md "Diálogo").
// Trabaja sobre una copia del catálogo; Aceptar manda una sola orden apply_structures (un paso de deshacer).
// Si el motor rechaza algo, el diálogo queda abierto con el error.
import { formatMeters } from "./storey-panel.js";
import { parseNumber } from "./infobox.js";

const $ = (id) => document.getElementById(id);
const DEFAULT_MATERIAL = "Hormigón";

export class StructuresDialog {
  constructor() {
    this.dialog = $("structures-dialog");
    $("sd-new").addEventListener("click", () => this.addStructure());
    $("sd-duplicate").addEventListener("click", () => this.duplicate());
    $("sd-rename").addEventListener("click", () => $("sd-name").focus());
    $("sd-delete").addEventListener("click", () => this.remove());
    $("sd-name").addEventListener("input", () => {
      const s = this.current();
      if (s) {
        s.name = $("sd-name").value;
        this.renderList();
      }
    });
    $("sd-add-layer").addEventListener("click", () => this.addLayer());
    $("sd-remove-layer").addEventListener("click", () => this.removeLayer());
    $("sd-up").addEventListener("click", () => this.moveLayer(-1));
    $("sd-down").addEventListener("click", () => this.moveLayer(1));
    $("sd-material-add").addEventListener("click", () => this.addMaterial());
    $("sd-ok").addEventListener("click", (event) => {
      event.preventDefault();
      this.accept();
    });
    $("sd-cancel").addEventListener("click", (event) => {
      event.preventDefault();
      this.dialog.close("cancel");
    });
    this.dialog.addEventListener("close", () => {
      if (this.resolve) this.resolve(this.result);
      this.resolve = null;
    });
  }

  // Abre el diálogo con el estado del motor. submit(payload) manda apply_structures y devuelve la respuesta.
  open(state, submit) {
    this.submit = submit;
    this.result = null;
    this.materials = state.materials.map((m) => ({ ...m, ref: null }));
    this.structures = state.structures.map((s) => ({
      id: s.id,
      ref: null,
      copy_of: null,
      name: s.name,
      walls: s.walls,
      original: JSON.stringify({ name: s.name, layers: s.layers.map((l) => [l.material_id, l.thickness]) }),
      layers: s.layers.map((l) => ({ material: l.material_id, thickness: l.thickness })),
    }));
    this.deleted = [];
    this.counter = 0;
    this.selected = this.sorted()[0] || null;
    this.layerIndex = 0;
    this.error("");
    this.render();
    this.dialog.showModal();
    return new Promise((resolve) => (this.resolve = resolve));
  }

  // ---------- datos ----------
  sorted() {
    return [...this.structures].sort((a, b) => a.name.localeCompare(b.name, "es", { sensitivity: "base" }));
  }

  current() {
    return this.selected;
  }

  defaultMaterial() {
    const found = this.materials.find((m) => m.name === DEFAULT_MATERIAL) || this.materials[0];
    return found ? found.id ?? found.ref : null;
  }

  materialKey(m) {
    return m.id !== null && m.id !== undefined ? m.id : m.ref;
  }

  error(text) {
    $("sd-error").textContent = text || "";
    $("sd-error").hidden = !text;
  }

  // ---------- estructuras ----------
  addStructure() {
    let n = 1;
    const names = new Set(this.structures.map((s) => s.name.toLowerCase()));
    while (names.has(`estructura ${n}`)) n += 1;
    const s = { id: null, ref: `s${++this.counter}`, copy_of: null, name: `Estructura ${n}`, walls: 0, original: null, layers: [{ material: this.defaultMaterial(), thickness: 0.2 }] };
    this.structures.push(s);
    this.selected = s;
    this.layerIndex = 0;
    this.error("");
    this.render();
  }

  duplicate() {
    const source = this.current();
    if (!source) return;
    const s = {
      id: null,
      ref: `s${++this.counter}`,
      copy_of: source.id,
      name: `${source.name} (copia)`,
      walls: 0,
      original: null,
      layers: source.layers.map((l) => ({ ...l })),
    };
    this.structures.push(s);
    this.selected = s;
    this.error("");
    this.render();
  }

  remove() {
    const s = this.current();
    if (!s) return;
    if (s.walls > 0) {
      this.error(`La estructura «${s.name}» ${s.walls === 1 ? "la usa 1 muro" : `la usan ${s.walls} muros`}; no se puede borrar.`);
      return;
    }
    this.structures = this.structures.filter((x) => x !== s);
    if (s.id !== null) this.deleted.push(s.id);
    this.selected = this.sorted()[0] || null;
    this.error("");
    this.render();
  }

  // ---------- capas ----------
  addLayer() {
    const s = this.current();
    if (!s) return;
    s.layers.splice(this.layerIndex + 1, 0, { material: this.defaultMaterial(), thickness: 0.1 });
    this.layerIndex += 1;
    this.render();
  }

  removeLayer() {
    const s = this.current();
    if (!s) return;
    if (s.layers.length <= 1) {
      this.error("La estructura tiene que tener al menos una capa.");
      return;
    }
    s.layers.splice(this.layerIndex, 1);
    this.layerIndex = Math.max(0, this.layerIndex - 1);
    this.error("");
    this.render();
  }

  moveLayer(step) {
    const s = this.current();
    const to = this.layerIndex + step;
    if (!s || to < 0 || to >= s.layers.length) return;
    [s.layers[this.layerIndex], s.layers[to]] = [s.layers[to], s.layers[this.layerIndex]];
    this.layerIndex = to;
    this.render();
  }

  // ---------- materiales ----------
  addMaterial() {
    const name = $("sd-material-name").value.trim();
    if (!name) {
      this.error("El nombre del material no puede quedar vacío.");
      return;
    }
    if (this.materials.some((m) => m.name.toLowerCase() === name.toLowerCase())) {
      this.error(`Ya existe un material llamado «${name}».`);
      return;
    }
    this.materials.push({ id: null, ref: `m${++this.counter}`, name, color: $("sd-material-color").value });
    $("sd-material-name").value = "";
    this.error("");
    this.render();
  }

  // ---------- Aceptar ----------
  payload() {
    const structures = [];
    for (const s of this.structures) {
      const layers = s.layers.map((l) => ({ material: l.material, thickness: l.thickness }));
      if (s.id === null) {
        structures.push({ id: null, ref: s.ref, name: s.name, copy_of: s.copy_of, layers });
      } else if (JSON.stringify({ name: s.name, layers: layers.map((l) => [l.material, l.thickness]) }) !== s.original) {
        structures.push({ id: s.id, name: s.name, layers });
      }
    }
    const materials = this.materials.filter((m) => m.id === null).map((m) => ({ ref: m.ref, name: m.name, color: m.color }));
    return { materials, structures, deleted: [...this.deleted] };
  }

  async accept() {
    // Espesores escritos en la tabla: tienen que ser números (las reglas de > 0 las comprueba el motor).
    if (this.structures.some((s) => s.layers.some((l) => Number.isNaN(l.thickness)))) {
      this.error("Escribe un número, por ejemplo 0,20.");
      return;
    }
    const payload = this.payload();
    if (!payload.materials.length && !payload.structures.length && !payload.deleted.length) {
      this.dialog.close("ok");
      return;
    }
    const response = await this.submit(payload);
    if (response && response.ok) {
      this.result = response;
      this.dialog.close("ok");
    } else {
      this.error(response ? response.error : "No se pudieron aplicar los cambios.");
    }
  }

  // ---------- dibujo ----------
  render() {
    this.renderList();
    const s = this.current();
    $("sd-name").value = s ? s.name : "";
    $("sd-name").disabled = !s;
    $("sd-layers-title").textContent = s ? `Capas de «${s.name}» (de exterior a interior)` : "Capas (de exterior a interior)";
    const body = $("sd-layers");
    body.innerHTML = "";
    if (s) {
      s.layers.forEach((layer, i) => {
        const row = document.createElement("tr");
        if (i === this.layerIndex) row.classList.add("selected");
        row.addEventListener("click", () => {
          if (this.layerIndex !== i) {
            this.layerIndex = i;
            this.render();
          }
        });
        const number = document.createElement("td");
        number.textContent = String(i + 1);
        const materialCell = document.createElement("td");
        const select = document.createElement("select");
        for (const m of this.materials) {
          const option = document.createElement("option");
          option.value = String(this.materialKey(m));
          option.textContent = m.name;
          select.appendChild(option);
        }
        select.value = String(layer.material);
        select.addEventListener("change", () => {
          const m = this.materials.find((x) => String(this.materialKey(x)) === select.value);
          layer.material = this.materialKey(m);
        });
        materialCell.appendChild(select);
        const thicknessCell = document.createElement("td");
        thicknessCell.className = "num";
        const input = document.createElement("input");
        input.type = "text";
        input.inputMode = "decimal";
        input.value = formatMeters(layer.thickness);
        input.addEventListener("change", () => {
          layer.thickness = parseNumber(input.value);
          this.renderTotal();
        });
        thicknessCell.appendChild(input);
        row.append(number, materialCell, thicknessCell);
        body.appendChild(row);
      });
    }
    this.renderTotal();
    for (const id of ["sd-duplicate", "sd-rename", "sd-delete", "sd-add-layer", "sd-remove-layer", "sd-up", "sd-down"]) $(id).disabled = !s;
  }

  renderList() {
    const list = $("sd-list");
    list.innerHTML = "";
    for (const s of this.sorted()) {
      const item = document.createElement("li");
      if (s === this.selected) item.classList.add("selected");
      const name = document.createElement("span");
      name.textContent = s.name;
      const total = document.createElement("span");
      total.textContent = formatMeters(s.layers.reduce((sum, l) => sum + (Number.isNaN(l.thickness) ? 0 : l.thickness), 0));
      item.append(name, total);
      item.addEventListener("click", () => {
        this.selected = s;
        this.layerIndex = 0;
        this.error("");
        this.render();
      });
      list.appendChild(item);
    }
  }

  renderTotal() {
    const s = this.current();
    const total = s ? s.layers.reduce((sum, l) => sum + (Number.isNaN(l.thickness) ? 0 : l.thickness), 0) : 0;
    $("sd-total").textContent = s ? `Espesor total: ${formatMeters(total)} m` : "";
  }
}
