// Planta del piso activo + vista 3D del edificio, en un solo WebGLRenderer con dos zonas (research R7).
// Navegación aprobada por el usuario (FR-025): MapControls en la planta y camera-controls en el 3D.
import * as THREE from "three";
import { MapControls } from "three/addons/controls/MapControls.js";
import CameraControls from "camera-controls";

THREE.Object3D.DEFAULT_UP.set(0, 0, 1); // IFC: Z hacia arriba
CameraControls.install({ THREE });

const PLAN_HALF_HEIGHT = 9; // m visibles hacia arriba y abajo con zoom 1

export class Viewports {
  constructor({ canvas, planDiv, view3dDiv, planLabel }) {
    this.canvas = canvas;
    this.planDiv = planDiv;
    this.view3dDiv = view3dDiv;
    this.planLabel = planLabel;
    this.groups = new Map(); // piso (id o "none") → THREE.Group
    this.activeStorey = null;
    this.activeElevation = 0;
    this.lastPlanVisible = [];
    this.last3dVisible = [];
    this.materials = { plan: (mesh) => mesh.userData.material, view3d: (mesh) => mesh.userData.material };
    this.raycaster = new THREE.Raycaster();

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color("#f4f4f2");
    this.scene.add(new THREE.HemisphereLight("#ffffff", "#b9b4aa", 1.6));
    const sun = new THREE.DirectionalLight("#ffffff", 1.4);
    sun.position.set(10, -14, 20);
    this.scene.add(sun);
    const grid = new THREE.GridHelper(200, 200, "#c9c5bd", "#e2dfd9"); // líneas cada 1,00 m (FR-009)
    grid.rotation.x = Math.PI / 2;
    this.scene.add(grid);
    // Vista previa del dibujo (función 002): solo en la planta, fuera de los grupos de pisos.
    this.overlay = new THREE.Group();
    this.overlay.renderOrder = 10;
    this.scene.add(this.overlay);

    // Planta: ortogonal, desde arriba, sin rotación; la rueda acerca hacia el ratón.
    this.planCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 1000);
    this.planCamera.up.set(0, 1, 0);
    this.planCamera.position.set(0, 0, 200);
    this.planControls = new MapControls(this.planCamera, planDiv);
    this.planControls.enableRotate = false;
    this.planControls.screenSpacePanning = true;
    this.planControls.zoomToCursor = true;
    this.planControls.mouseButtons = { LEFT: -1, MIDDLE: THREE.MOUSE.PAN, RIGHT: -1 };
    this.planControls.addEventListener("change", () => this.draw());

    // 3D: girar alrededor del punto señalado, desplazar, acercar hacia el ratón, sin pasar bajo el suelo.
    this.camera3d = new THREE.PerspectiveCamera(40, 1, 0.1, 1000);
    this.controls3d = new CameraControls(this.camera3d, view3dDiv);
    this.controls3d.mouseButtons.left = CameraControls.ACTION.ROTATE;
    this.controls3d.mouseButtons.middle = CameraControls.ACTION.TRUCK;
    this.controls3d.mouseButtons.right = CameraControls.ACTION.TRUCK;
    this.controls3d.mouseButtons.wheel = CameraControls.ACTION.DOLLY;
    this.controls3d.dollyToCursor = true;
    this.controls3d.maxPolarAngle = THREE.MathUtils.degToRad(88);
    this.controls3d.minDistance = 0.5;
    this.controls3d.maxDistance = 500;
    this.controls3d.smoothTime = 0.12;
    this.controls3d.draggingSmoothTime = 0.06;
    this.controls3d.setLookAt(15, -13, 11, 3, 2, 1.5, false);

    view3dDiv.addEventListener(
      "pointerdown",
      (event) => {
        const rotate = event.button === 0 || (event.button === 1 && event.shiftKey);
        this.controls3d.mouseButtons.middle = event.shiftKey ? CameraControls.ACTION.ROTATE : CameraControls.ACTION.TRUCK;
        if (event.button === 0) this.down3d = { x: event.clientX, y: event.clientY };
        if (!rotate) return;
        const hit = this.hit3d(event);
        if (hit) this.controls3d.setOrbitPoint(hit.point.x, hit.point.y, hit.point.z);
      },
      { capture: true }
    );
    // Clic sin arrastre en el 3D (menos de 4 px): elige un elemento (función 002, research R12).
    view3dDiv.addEventListener(
      "pointerup",
      (event) => {
        const down = this.down3d;
        this.down3d = null;
        if (event.button !== 0 || !down || Math.hypot(event.clientX - down.x, event.clientY - down.y) >= 4) return;
        if (this.on3dClick) this.on3dClick(event, this.hit3d(event));
      },
      { capture: true }
    );

    new ResizeObserver(() => this.draw()).observe(canvas);
    const timer = new THREE.Timer();
    const loop = (time) => {
      timer.update(time);
      if (this.controls3d.update(timer.getDelta())) this.draw();
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }

  group(storeyId) {
    const key = storeyId ?? "none";
    if (!this.groups.has(key)) {
      const group = new THREE.Group();
      group.userData.storeyId = storeyId;
      this.groups.set(key, group);
      this.scene.add(group);
    }
    return this.groups.get(key);
  }

  meshes() {
    return [...this.groups.values()].flatMap((group) => group.children);
  }

  // Quién decide el material de cada malla en cada vista (meshes.js: capas, colores y selección).
  setMaterialProvider(provider) {
    this.materials = provider;
  }

  setActiveStorey(id, name, elevation = 0) {
    this.activeStorey = id;
    this.activeElevation = elevation;
    this.planLabel.textContent = name ? `Planta — ${name}` : "Planta";
    this.draw();
  }

  // ---------- ratón (función 002, research R12) ----------
  pointer(event, div) {
    const box = div.getBoundingClientRect();
    return new THREE.Vector2(((event.clientX - box.left) / box.width) * 2 - 1, -((event.clientY - box.top) / box.height) * 2 + 1);
  }

  // Punto de la planta bajo el ratón, sobre el plano de la cota del piso activo: {x, y} en metros.
  planPoint(event) {
    this.raycaster.setFromCamera(this.pointer(event, this.planDiv), this.planCamera);
    const plane = new THREE.Plane(new THREE.Vector3(0, 0, 1), -this.activeElevation);
    const point = this.raycaster.ray.intersectPlane(plane, new THREE.Vector3());
    return point ? { x: point.x, y: point.y } : null;
  }

  // Tamaño de un píxel de la planta, en metros.
  pixelsToMeters(px) {
    const visible = (this.planCamera.top - this.planCamera.bottom) / this.planCamera.zoom;
    return (px * visible) / Math.max(1, this.planDiv.clientHeight);
  }

  // Elemento de la planta bajo el ratón (solo el piso activo).
  hitPlan(event) {
    const group = this.groups.get(this.activeStorey ?? "none");
    if (!group) return null;
    this.raycaster.setFromCamera(this.pointer(event, this.planDiv), this.planCamera);
    return this.raycaster.intersectObjects(group.children, false)[0] || null;
  }

  // Elemento del 3D bajo el ratón (todos los pisos).
  hit3d(event) {
    this.raycaster.setFromCamera(this.pointer(event, this.view3dDiv), this.camera3d);
    return this.raycaster.intersectObjects(this.meshes(), false)[0] || null;
  }

  // Para la prueba del programa: dónde está un punto de la planta en la pantalla.
  worldToClient(x, y) {
    const ndc = new THREE.Vector3(x, y, this.activeElevation).project(this.planCamera);
    const box = this.planDiv.getBoundingClientRect();
    return { clientX: box.left + ((ndc.x + 1) / 2) * box.width, clientY: box.top + ((1 - ndc.y) / 2) * box.height };
  }

  draw() {
    const width = this.canvas.clientWidth;
    const height = this.canvas.clientHeight;
    if (!width || !height) return;
    this.renderer.setSize(width, height, false);
    this.renderer.setScissorTest(true);
    const half = Math.floor(width / 2);

    // Planta: solo el piso activo, con los sólidos en gris oscuro.
    const aspect = half / height;
    this.planCamera.left = -PLAN_HALF_HEIGHT * aspect;
    this.planCamera.right = PLAN_HALF_HEIGHT * aspect;
    this.planCamera.top = PLAN_HALF_HEIGHT;
    this.planCamera.bottom = -PLAN_HALF_HEIGHT;
    this.planCamera.updateProjectionMatrix();
    this.lastPlanVisible = [];
    for (const [key, group] of this.groups) {
      group.visible = key === this.activeStorey;
      if (group.visible && group.children.length) this.lastPlanVisible.push(key);
    }
    for (const mesh of this.meshes()) mesh.material = this.materials.plan(mesh);
    this.overlay.visible = true;
    this.renderer.setViewport(0, 0, half, height);
    this.renderer.setScissor(0, 0, half, height);
    this.renderer.render(this.scene, this.planCamera);

    // 3D: todo el edificio.
    this.last3dVisible = [];
    for (const [key, group] of this.groups) {
      group.visible = true;
      if (group.children.length) this.last3dVisible.push(key);
    }
    for (const mesh of this.meshes()) mesh.material = this.materials.view3d(mesh);
    this.overlay.visible = false;
    this.camera3d.aspect = (width - half) / height;
    this.camera3d.updateProjectionMatrix();
    this.renderer.setViewport(half, 0, width - half, height);
    this.renderer.setScissor(half, 0, width - half, height);
    this.renderer.render(this.scene, this.camera3d);
  }

  // Encuadrar: la planta en el piso activo, el 3D en todo el edificio.
  fit({ animate = true } = {}) {
    const all = new THREE.Box3();
    const storey = new THREE.Box3();
    for (const mesh of this.meshes()) {
      all.expandByObject(mesh);
      if (mesh.userData.storeyId === this.activeStorey) storey.expandByObject(mesh);
    }
    if (all.isEmpty()) return;
    const box = storey.isEmpty() ? all : storey;
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const aspect = this.planDiv.clientWidth / Math.max(1, this.canvas.clientHeight);
    this.planControls.target.set(center.x, center.y, 0);
    this.planCamera.position.set(center.x, center.y, 200);
    this.planCamera.zoom = Math.min(PLAN_HALF_HEIGHT / (Math.max(size.y, 1) * 0.75), (PLAN_HALF_HEIGHT * aspect) / (Math.max(size.x, 1) * 0.75));
    this.planCamera.updateProjectionMatrix();
    this.planControls.update();
    const middle = all.getCenter(new THREE.Vector3());
    const radius = all.getSize(new THREE.Vector3()).length() / 2;
    const distance = (radius / Math.sin(THREE.MathUtils.degToRad(this.camera3d.fov / 2))) * 1.1;
    const eye = middle.clone().add(new THREE.Vector3(1, -1.1, 0.8).normalize().multiplyScalar(distance));
    this.controls3d.setLookAt(eye.x, eye.y, eye.z, middle.x, middle.y, middle.z, animate);
    this.controls3d.update(0);
    this.draw();
  }

  // Para la prueba del programa: pisos visibles en la última pasada de la planta.
  debugVisiblePlanStoreys() {
    return [...this.lastPlanVisible];
  }

  // Para la prueba del programa: pisos con elementos dibujados en la última pasada del 3D.
  debugVisible3dStoreys() {
    return [...this.last3dVisible];
  }
}
