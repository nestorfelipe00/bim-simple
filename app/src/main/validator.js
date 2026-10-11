// Valida un IFC guardado (IFC4 + reglas EXPRESS) en un segundo motor, para no bloquear al principal (research R6).
const { Engine } = require("./engine");

async function validateFile(pythonExe, logFile, filePath) {
  const validator = new Engine({ pythonExe, logFile, restartOnCrash: false });
  try {
    await validator.start();
    const response = await validator.request("validate_file", { path: filePath });
    return response.ok ? response.result : { errors: null, error: response.error };
  } finally {
    validator.stop();
  }
}

module.exports = { validateFile };
