// Mallas que manda el motor (data-model.md §5), agrupadas por piso en la escena.
// Función 002: los muros editables traen un grupo por capa; cada grupo usa el color de su material, en el 3D
// (MeshStandardMaterial) y en la planta (MeshBasicMaterial). La selección se ve en azul en las dos vistas.
import * as THREE from "three";

const MATERIALS = {
  IfcWall: new THREE.MeshStandardMaterial({ color: "#ddd6ca", roughness: 0.9 }),
  IfcSlab: new THREE.MeshStandardMaterial({ color: "#cfcbc4", roughness: 0.9 }),
  IfcColumn: new THREE.MeshStandardMaterial({ color: "#c9c2b6", roughness: 0.9 }),
  IfcDoor: new THREE.MeshStandardMaterial({ color: "#b8926a", roughness: 0.8 }),
  IfcWindow: new THREE.MeshStandardMaterial({ color: "#a9c6dd", roughness: 0.4 }),
};
const DEFAULT_MATERIAL = new THREE.MeshStandardMaterial({ color: "#d9d9d6", roughness: 0.9 });
const PLAN_DEFAULT = new THREE.MeshBasicMaterial({ color: "#4a4741" }); // relleno oscuro en planta (función 001)
const SELECTED_COLOR = "#2f6fd6"; // contracts/ui.md, "Selección"
const SELECTED_3D = new THREE.MeshStandardMaterial({ color: SELECTED_COLOR, roughness: 0.7 });
const SELECTED_PLAN = new THREE.MeshBasicMaterial({ color: SELECTED_COLOR });
const EDGE_MATERIAL = new THREE.LineBasicMaterial({ color: "#3b3833" });
const UNKNOWN_COLOR = "#d9d9d6";

function decode(base64, Type) {
  const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
  return new Type(bytes.buffer);
}

export class MeshStore {
  constructor(viewports) {
    this.viewports = viewports;
    this.byId = new Map();
    this.colors = new Map(); // material_id → "#rrggbb"
    this.standard = new Map(); // material_id → MeshStandardMaterial
    this.basic = new Map(); // material_id → MeshBasicMaterial
    this.selected = new Set();
    viewports.setMaterialProvider({
      plan: (mesh) => (this.selected.has(mesh.userData.id) ? SELECTED_PLAN : mesh.userData.planMaterial),
      view3d: (mesh) => (this.selected.has(mesh.userData.id) ? SELECTED_3D : mesh.userData.material),
    });
  }

  get size() {
    return this.byId.size;
  }

  // Colores de state.materials; actualiza los materiales ya creados.
  setMaterials(list) {
    for (const { id, color } of list || []) {
      this.colors.set(id, color);
      if (this.standard.has(id)) this.standard.get(id).color.set(color);
      if (this.basic.has(id)) this.basic.get(id).color.set(color);
    }
  }

  materialFor(materialId, plan) {
    const cache = plan ? this.basic : this.standard;
    if (!cache.has(materialId)) {
      const color = this.colors.get(materialId) || UNKNOWN_COLOR;
      cache.set(materialId, plan ? new THREE.MeshBasicMaterial({ color }) : new THREE.MeshStandardMaterial({ color, roughness: 0.9 }));
    }
    return cache.get(materialId);
  }

  clear() {
    for (const id of [...this.byId.keys()]) this.remove(id);
  }

  remove(id) {
    const mesh = this.byId.get(id);
    if (!mesh) return;
    mesh.parent.remove(mesh);
    mesh.geometry.dispose();
    mesh.children.forEach((child) => child.geometry.dispose());
    this.byId.delete(id);
  }

  // result = { meshes, existing_ids } de la orden "meshes".
  apply(result) {
    for (const item of result.meshes) {
      this.remove(item.id);
      const indexed = new THREE.BufferGeometry();
      indexed.setAttribute("position", new THREE.BufferAttribute(decode(item.vertices, Float32Array), 3));
      indexed.setIndex(new THREE.BufferAttribute(decode(item.faces, Uint32Array), 1));
      const groups = item.groups || [];
      // Antes de toNonIndexed, que copia los grupos con los mismos rangos (three/src/core/BufferGeometry.js:1123).
      groups.forEach((group, i) => indexed.addGroup(group.start, group.count, i));
      const geometry = indexed.toNonIndexed();
      geometry.computeVertexNormals();
      indexed.dispose();
      const material = groups.length ? groups.map((g) => this.materialFor(g.material_id, false)) : MATERIALS[item.ifc_class] || DEFAULT_MATERIAL;
      const planMaterial = groups.length ? groups.map((g) => this.materialFor(g.material_id, true)) : PLAN_DEFAULT;
      const mesh = new THREE.Mesh(geometry, material);
      mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(geometry, 20), EDGE_MATERIAL));
      mesh.userData = { id: item.id, storeyId: item.storey_id, ifcClass: item.ifc_class, material, planMaterial, wall: item.wall || null };
      this.viewports.group(item.storey_id).add(mesh);
      this.byId.set(item.id, mesh);
    }
    const existing = new Set(result.existing_ids);
    for (const id of [...this.byId.keys()]) if (!existing.has(id)) this.remove(id);
    for (const id of [...this.selected]) if (!this.byId.has(id)) this.selected.delete(id);
    this.viewports.draw();
  }

  setSelected(ids) {
    this.selected = new Set(ids.filter((id) => this.byId.has(id)));
    this.viewports.draw();
  }

  // Datos de los muros (data-model.md §6) de un piso, o de todos.
  walls(storeyId) {
    const result = [];
    for (const mesh of this.byId.values()) {
      const wall = mesh.userData.wall;
      if (wall && (storeyId === undefined || mesh.userData.storeyId === storeyId)) result.push(wall);
    }
    return result;
  }

  wall(id) {
    const mesh = this.byId.get(id);
    return mesh ? mesh.userData.wall : null;
  }
}
