// Prueba del programa con la ventana oculta (constitución, Principio V). La carga app.js con ?test=1.
// Recorre las acciones como lo haría el usuario, captura la pantalla y escribe app/test-output/resultado.json.
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const $ = (id) => document.getElementById(id);
const NAVIGATOR_LIMIT_MS = 200; // SC-004

const EXPECTED_MENUS = [
  { label: "Archivo", items: ["Nuevo proyecto", "Abrir IFC…", "Guardar IFC", "Guardar IFC como…", "Salir"] },
  { label: "Edición", items: ["Deshacer", "Rehacer"] },
  { label: "Ayuda", items: ["Acerca de BIM Simple"] },
];

export async function run(app) {
  const result = { steps: [], captures: [], failures: 0, closeWithChanges: false };
  const t = {
    app,
    step(section, name, ok, detail) {
      result.steps.push({ section, name, ok: !!ok, detail });
      if (!ok) result.failures += 1;
    },
    // Acción del navegador de pisos: además de su comprobación, no puede tardar más de 200 ms (SC-004).
    async navigatorAction(section, name, action, check) {
      const started = performance.now();
      const response = await action();
      const ms = Math.round(performance.now() - started);
      const detail = { ms, error: response && !response.ok ? response.error : undefined };
      t.step(section, `${name} (${ms} ms)`, check(response) && ms <= NAVIGATOR_LIMIT_MS, detail);
      return response;
    },
    async capture(name) {
      app.viewports.draw();
      await sleep(600);
      result.captures.push({ name, size: await bim.test.capture(name) });
    },
    tableRows() {
      return [...$("storeys").querySelectorAll("tr")].map((tr) => [...tr.children].map((td) => td.textContent));
    },
    sleep,
    result,
  };

  try {
    await bim.test.capture("calentamiento"); // la primera captura de una ventana oculta devuelve un cuadro viejo
    await environment(t);
    for (const section of SECTIONS) await section(t);
  } catch (error) {
    t.step("Error", "Excepción durante la prueba", false, String((error && error.stack) || error));
  }
  await bim.test.finish(result);
}

// Secciones de cada historia (se agregan en orden: Historia 1, 2, 3, 4, Motor detenido).
const SECTIONS = [];
export function addSection(fn) {
  SECTIONS.push(fn);
}

async function environment(t) {
  const S = "Entorno";
  t.step(S, `Motor listo en menos de 10 s (SC-007): ${t.app.ready.ready_ms} ms`, t.app.ready.ready_ms < 10000);
  t.step(S, "IfcOpenShell 0.9.0 en el motor", t.app.ready.ifcopenshell === "0.9.0", t.app.ready.ifcopenshell);
  const menus = await bim.test.menuLabels();
  t.step(S, "Menús Archivo, Edición y Ayuda con sus textos (FR-003)", JSON.stringify(menus) === JSON.stringify(EXPECTED_MENUS), menus);
  t.step(S, "Título sin proyecto: «BIM Simple»", (await bim.test.windowTitle()) === "BIM Simple");
  t.step(S, "Arranca sin proyecto (FR-006)", $("project").textContent === "No hay ningún proyecto abierto" && !t.app.getState().has_project);
  t.step(S, "Vistas vacías al arrancar (FR-006)", t.app.meshes.size === 0);
  await t.capture("base");
}

// ---------- Historia 1: abrir BIM Simple, empezar un proyecto y guardarlo ----------
async function waitFor(condition, timeoutMs = 10000) {
  const started = performance.now();
  while (performance.now() - started < timeoutMs) {
    if (condition()) return true;
    await sleep(100);
  }
  return false;
}

addSection(async function historia1(t) {
  const S = "Historia 1";
  await t.app.handleAction("new"); // Archivo > Nuevo proyecto
  t.step(S, "Nuevo proyecto: «● Planta Baja | 0,00 | 3,00» (FR-007)", JSON.stringify(t.tableRows()) === JSON.stringify([["● Planta Baja", "0,00", "3,00"]]), t.tableRows());
  t.step(S, "Título: «Proyecto sin guardar — BIM Simple» (FR-004)", (await bim.test.windowTitle()) === "Proyecto sin guardar — BIM Simple", await bim.test.windowTitle());

  const output = await bim.test.outputDir();
  const path = `${output}\\prueba.ifc`;
  await bim.test.answerDialogs([path]); // el diálogo "Guardar IFC como" responde con esta ruta
  const saved = await t.app.handleAction("save"); // Guardar IFC sin ruta → Guardar como
  t.step(S, "Guardar IFC en un proyecto nuevo pide la ruta y guarda (FR-009)", saved && saved.ok && saved.result.path === path, saved);
  t.step(S, "Título: «prueba.ifc — BIM Simple»", (await bim.test.windowTitle()) === "prueba.ifc — BIM Simple", await bim.test.windowTitle());
  const validated = await waitFor(() => document.getElementById("messages").textContent === "Guardado. Validación IFC4: 0 errores.");
  t.step(S, "Validación en segundo plano: «Guardado. Validación IFC4: 0 errores.» (SC-003)", validated, document.getElementById("messages").textContent);

  await bim.about(); // Ayuda > Acerca de BIM Simple
  const log = await bim.test.dialogLog();
  const about = log.dialogs.find((d) => d.title === "Acerca de BIM Simple");
  t.step(S, "Acerca de: aviso LGPL-3.0 de IfcOpenShell con su enlace (FR-003, Principio VI)", about && about.message.includes("IfcOpenShell 0.9.0 — LGPL-3.0") && about.message.includes("https://github.com/IfcOpenShell/IfcOpenShell"), about);
  await t.capture("h1");
});

addSection(async function historia1Panel(t) {
  const S = "Historia 1";
  const actions = document.getElementById("no-project-actions");
  t.step(S, "Con proyecto abierto se ocultan «Nuevo proyecto» y «Abrir IFC…» del panel (ui.md)", getComputedStyle(actions).display === "none");
});
