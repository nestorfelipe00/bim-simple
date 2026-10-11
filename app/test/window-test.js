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
    if (result.closeWithChanges) {
      // Deja un proyecto con cambios sin guardar para el último paso: cerrar con la X (FR-010).
      await app.handleAction("new");
      await app.handleAction("add-above");
    }
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

// ---------- Historia 2: organizar los pisos ----------
async function editSelected(t, rowName, values) {
  // Selecciona la fila con un clic, abre "Editar piso…", completa el diálogo y pulsa Aceptar.
  const row = [...document.querySelectorAll("#storeys tr")].find((tr) => tr.firstChild.textContent.replace("● ", "") === rowName);
  row.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  const pending = t.app.handleAction("edit");
  await sleep(50);
  for (const [field, value] of Object.entries(values)) document.getElementById(`edit-${field}`).value = value;
  const started = performance.now();
  document.getElementById("edit-ok").click();
  const response = await pending;
  // SC-004 mide la acción (orden, respuesta y redibujo: total_ms de dispatch). El cierre del diálogo en una
  // ventana oculta llega con ~1 s de retraso por cómo Chromium agenda esas tareas; se registra aparte.
  return { response, ms: response ? response.total_ms : null, withDialogMs: Math.round(performance.now() - started) };
}

addSection(async function historia2(t) {
  const S = "Historia 2";
  await t.app.handleAction("new");
  await t.navigatorAction(S, "Agregar piso arriba", () => t.app.handleAction("add-above"), (r) => r.ok);
  await t.navigatorAction(S, "Agregar piso arriba", () => t.app.handleAction("add-above"), (r) => r.ok);
  await t.navigatorAction(S, "Agregar piso abajo", () => t.app.handleAction("add-below"), (r) => r.ok);
  const expected = [["Piso 2", "6,00", "3,00"], ["Piso 1", "3,00", "3,00"], ["● Planta Baja", "0,00", "3,00"], ["Sótano 1", "-3,00", "3,00"]];
  t.step(S, "Cuatro pisos en orden, el más alto arriba (FR-012 a FR-014)", JSON.stringify(t.tableRows()) === JSON.stringify(expected), t.tableRows());

  const edit = await editSelected(t, "Planta Baja", { height: "3,50" });
  t.step(S, `Editar piso: altura de Planta Baja 3,50 → Piso 1 a 3,50 y Piso 2 a 6,50 (FR-016) (${edit.ms} ms)`,
    edit.response.ok && edit.ms <= 200 && JSON.stringify(t.tableRows().slice(0, 3)) === JSON.stringify([["Piso 2", "6,50", "3,00"], ["Piso 1", "3,50", "3,00"], ["● Planta Baja", "0,00", "3,50"]]), t.tableRows());

  const before = JSON.stringify(t.tableRows());
  const invalid = await editSelected(t, "Piso 1", { elevation: "0,00" });
  t.step(S, "Cota inválida: mensaje exacto y la tabla no cambia",
    !invalid.response.ok && document.getElementById("messages").textContent === "La cota debe ser mayor que la del piso de abajo («Planta Baja», 0,00 m)." && JSON.stringify(t.tableRows()) === before,
    document.getElementById("messages").textContent);

  const sotano = [...document.querySelectorAll("#storeys tr")].find((tr) => tr.firstChild.textContent === "Sótano 1");
  sotano.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await t.navigatorAction(S, "Borrar «Sótano 1» (sin elementos, sin preguntar)", () => t.app.handleAction("delete"), (r) => r.ok && t.tableRows().length === 3);

  await t.navigatorAction(S, "Edición > Deshacer: vuelve «Sótano 1»", () => t.app.handleAction("undo"), (r) => r.ok && t.tableRows().length === 4);
  await t.navigatorAction(S, "Edición > Rehacer: se borra de nuevo", () => t.app.handleAction("redo"), (r) => r.ok && t.tableRows().length === 3);
  t.step(S, "Título con cambios sin guardar empieza con «* »", (await bim.test.windowTitle()).startsWith("* "), await bim.test.windowTitle());

  // Pregunta por cambios sin guardar (FR-010): Nuevo proyecto + Cancelar no cambia nada.
  const rows = JSON.stringify(t.tableRows());
  await bim.test.answerDialogs(["Cancelar"]);
  await t.app.handleAction("new");
  const log = await bim.test.dialogLog();
  const last = log.dialogs[log.dialogs.length - 1];
  t.step(S, "Nuevo proyecto con cambios: pregunta «¿Guardar cambios antes de cerrar?» y «Cancelar» no cambia nada",
    last && last.message === "¿Guardar cambios antes de cerrar?" && last.answer === "Cancelar" && JSON.stringify(t.tableRows()) === rows, last);
  await t.capture("h2");
  t.result.closeWithChanges = true; // el último paso de la prueba cierra la ventana con cambios (lo registra el proceso principal)
});
