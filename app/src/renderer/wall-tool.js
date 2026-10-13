// Herramienta Muro (función 002; FR-005 a FR-010; contracts/ui.md "Dibujo en la planta"; research R12).
// La vista previa y el imán son cálculos de pantalla: lo único que la interfaz dibuja sin que exista en el IFC
// (constitución, Principio I). Cada clic manda create_wall al motor, que crea el muro y lo une en las esquinas.
import * as THREE from "three";
import { formatMeters } from "./storey-panel.js";
import { parseNumber } from "./infobox.js";

const SNAP_PX = 10; // FR-009
const GRID = 0.1; // m (FR-009)
const MIN_LENGTH = 0.01; // m (spec, casos límite)
const PREVIEW_FILL = new THREE.MeshBasicMaterial({ color: "#2f6fd6", transparent: true, opacity: 0.25, depthTest: false });
const PREVIEW_LINE = new THREE.LineBasicMaterial({ color: "#2f6fd6", depthTest: false });
const MARKER_LINE = new THREE.LineBasicMaterial({ color: "#d4482c", depthTest: false });

const offsetFor = (reference, total) => ({ exterior: 0, center: total / 2, interior: total })[reference];

export class WallTool {
  constructor({ viewports, meshes, infobox, getState, onCreate, showMessage }) {
    this.viewports = viewports;
    this.meshes = meshes;
    this.infobox = infobox;
    this.getState = getState;
    this.onCreate = onCreate;
    this.showMessage = showMessage;
    this.label = document.getElementById("draw-label");
    this.chain = null; // { first, last, count }
    this.typed = "";
    this.point = null; // último punto resuelto (con imán)
    this.raw = null; // último punto del ratón sin imán
    this.snap = null; // "endpoint" | "grid" | null
    this.busy = false;
  }

  // ---------- puntos ----------
  activeWalls() {
    return this.meshes.walls(this.getState().active_storey_id);
  }

  // Imán (FR-009) y Shift (FR-008).
  resolve(raw, shift) {
    const tolerance = this.viewports.pixelsToMeters(SNAP_PX);
    if (this.chain && shift) {
      const last = this.chain.last;
      const angle = Math.round(Math.atan2(raw.y - last.y, raw.x - last.x) / (Math.PI / 4)) * (Math.PI / 4);
      const dir = { x: Math.cos(angle), y: Math.sin(angle) };
      const along = Math.round(((raw.x - last.x) * dir.x + (raw.y - last.y) * dir.y) / GRID) * GRID;
      this.snap = "grid";
      return { x: last.x + dir.x * along, y: last.y + dir.y * along };
    }
    let best = null;
    for (const wall of this.activeWalls()) {
      for (const end of [wall.start, wall.end]) {
        if (!end) continue;
        const d = Math.hypot(end[0] - raw.x, end[1] - raw.y);
        if (d <= tolerance && (!best || d < best.d)) best = { d, x: end[0], y: end[1] };
      }
    }
    if (best) {
      this.snap = "endpoint";
      return { x: best.x, y: best.y };
    }
    const grid = { x: Math.round(raw.x / GRID) * GRID, y: Math.round(raw.y / GRID) * GRID };
    if (Math.hypot(grid.x - raw.x, grid.y - raw.y) <= tolerance) {
      this.snap = "grid";
      return grid;
    }
    this.snap = null;
    return { x: raw.x, y: raw.y };
  }

  // ---------- eventos (los manda app.js; la prueba del programa los llama igual) ----------
  pointerMove(event) {
    const raw = this.viewports.planPoint(event);
    if (!raw) return;
    this.raw = raw;
    this.shift = !!event.shiftKey;
    this.point = this.resolve(raw, this.shift);
    this.updatePreview(event);
  }

  async pointerDown(event) {
    if (event.button === 2) return this.cancel();
    if (event.button !== 0 || this.busy) return null;
    this.pointerMove(event);
    const point = this.point;
    if (!point) return null;
    if (!this.chain) {
      this.chain = { first: point, last: point, count: 0 };
      this.updatePreview(event);
      return null;
    }
    const closing = this.chain.count > 0 && Math.hypot(point.x - this.chain.first.x, point.y - this.chain.first.y) <= this.viewports.pixelsToMeters(SNAP_PX);
    const response = await this.create(this.chain.last, closing ? this.chain.first : point);
    if (closing && response && response.ok) this.cancel();
    return response;
  }

  // Esc, Enter, dígitos, coma, punto y Retroceso. Devuelve true si la tecla era de la herramienta.
  async key(event) {
    if (event.key === "Escape") {
      this.cancel();
      return true;
    }
    if (!this.chain) return false;
    if (/^[0-9]$/.test(event.key) || event.key === "," || event.key === ".") {
      this.typed += event.key;
      this.updatePreview();
      return true;
    }
    if (event.key === "Backspace") {
      this.typed = this.typed.slice(0, -1);
      this.updatePreview();
      return true;
    }
    if (event.key === "Enter" && this.typed) {
      const length = parseNumber(this.typed);
      this.typed = "";
      if (!(length > 0)) {
        this.showMessage("La longitud debe ser mayor que 0.", true);
        this.updatePreview();
        return true;
      }
      const last = this.chain.last;
      const target = this.point || this.raw || { x: last.x + 1, y: last.y };
      let dx = target.x - last.x;
      let dy = target.y - last.y;
      const norm = Math.hypot(dx, dy);
      if (norm < 1e-9) [dx, dy] = [1, 0];
      else [dx, dy] = [dx / norm, dy / norm];
      await this.create(last, { x: last.x + dx * length, y: last.y + dy * length });
      return true;
    }
    return false;
  }

  async create(a, b) {
    if (Math.hypot(b.x - a.x, b.y - a.y) < MIN_LENGTH) return null; // no se manda (spec, casos límite)
    this.busy = true;
    try {
      const response = await this.onCreate([a.x, a.y], [b.x, b.y]);
      if (response && response.ok && this.chain) {
        this.chain.last = b;
        this.chain.count += 1;
      }
      this.updatePreview();
      return response;
    } finally {
      this.busy = false;
    }
  }

  cancel() {
    this.chain = null;
    this.typed = "";
    this.clearPreview();
    this.label.hidden = true;
    return null;
  }

  // ---------- vista previa ----------
  clearPreview() {
    for (const child of [...this.viewports.overlay.children]) {
      this.viewports.overlay.remove(child);
      child.geometry.dispose();
    }
    this.viewports.draw();
  }

  updatePreview(event) {
    this.clearPreview();
    const z = this.viewports.activeElevation + 0.01;
    if (this.point) this.addMarker(this.point, z);
    if (this.chain && this.point) {
      this.addWall(this.chain.last, this.point, z);
      const length = Math.hypot(this.point.x - this.chain.last.x, this.point.y - this.chain.last.y);
      this.label.textContent = this.typed ? `Longitud: ${this.typed}` : `${formatMeters(length)} m`;
      this.label.hidden = false;
      if (event && event.clientX !== undefined) {
        const box = this.viewports.planDiv.getBoundingClientRect();
        this.label.style.left = `${event.clientX - box.left + 14}px`;
        this.label.style.top = `${event.clientY - box.top + 14}px`;
      }
    } else {
      this.label.hidden = true;
    }
    this.viewports.draw();
  }

  addMarker(point, z) {
    if (!this.snap) return;
    const s = this.viewports.pixelsToMeters(5);
    const points =
      this.snap === "endpoint"
        ? [[-s, -s], [s, -s], [s, s], [-s, s], [-s, -s]]
        : [[-s, 0], [s, 0], [0, 0], [0, -s], [0, s]];
    const geometry = new THREE.BufferGeometry().setFromPoints(points.map(([x, y]) => new THREE.Vector3(point.x + x, point.y + y, z)));
    const marker = new THREE.Line(geometry, MARKER_LINE);
    marker.renderOrder = 12;
    this.viewports.overlay.add(marker);
  }

  // Franja del muro con sus capas, según el espesor y la línea de referencia del Info Box (FR-006, FR-012).
  addWall(a, b, z) {
    const length = Math.hypot(b.x - a.x, b.y - a.y);
    if (length < 1e-6) return;
    const dir = { x: (b.x - a.x) / length, y: (b.y - a.y) / length };
    const normal = { x: -dir.y, y: dir.x }; // +Y local: izquierda del sentido de dibujo
    const thicknesses = this.infobox.toolLayers();
    const total = thicknesses.reduce((sum, t) => sum + t, 0);
    const top = offsetFor(this.infobox.toolValues().reference, total); // el muro crece hacia −Y (NEGATIVE)
    const at = (p, y) => new THREE.Vector3(p.x + normal.x * y, p.y + normal.y * y, z);
    const outline = [at(a, top), at(b, top), at(b, top - total), at(a, top - total)];
    const shape = new THREE.Shape(outline.map((v) => new THREE.Vector2(v.x, v.y)));
    const fill = new THREE.Mesh(new THREE.ShapeGeometry(shape), PREVIEW_FILL);
    fill.position.z = z;
    fill.renderOrder = 10;
    this.viewports.overlay.add(fill);
    const line = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(outline), PREVIEW_LINE);
    line.renderOrder = 11;
    this.viewports.overlay.add(line);
    let y = top;
    for (const t of thicknesses.slice(0, -1)) {
      y -= t;
      const divider = new THREE.Line(new THREE.BufferGeometry().setFromPoints([at(a, y), at(b, y)]), PREVIEW_LINE);
      divider.renderOrder = 11;
      this.viewports.overlay.add(divider);
    }
  }
}
