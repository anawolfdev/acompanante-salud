// Prueba 18A del acompañante de salud.
// Lee citas de mentira de D1 y manda un aviso a Telegram.
// Como mucho manda 6 mensajes; después no manda más aunque el cron siga puesto.
// El tope se reserva ANTES de mandar (fila en la tabla envios), así dos
// ejecuciones a la vez no pueden pasarse del límite.
// Solo manda al chat que diga el secreto TELEGRAM_CHAT_ID.

var DIAS = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];
var MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
var MAX_MENSAJES = 6;

// "AAAA-MM-DD HH:MM" en hora de Madrid.
function ahoraMadrid() {
  return new Date().toLocaleString("sv-SE", { timeZone: "Europe/Madrid" }).slice(0, 16);
}

// De "2026-11-20 10:00" a "viernes 20 de noviembre a las 10:00".
function formatoBonito(fechaHora) {
  var partes = fechaHora.split(" ");
  var fecha = partes[0].split("-");
  var aaaa = Number(fecha[0]);
  var mm = Number(fecha[1]);
  var dd = Number(fecha[2]);
  var diaSemana = new Date(Date.UTC(aaaa, mm - 1, dd)).getUTCDay();
  var horaSinCero = partes[1].replace(/^0/, "");
  return DIAS[diaSemana] + " " + dd + " de " + MESES[mm - 1] + " a las " + horaSinCero;
}

export default {
  async scheduled(event, env, ctx) {
    // Reservar un hueco ANTES de mandar: cada ejecución inserta su fila y
    // solo mandan las 6 primeras. Si Telegram falla, ese hueco se pierde
    // (mejor mandar de menos que de más en una prueba).
    var reserva = await env.DB.prepare("INSERT INTO envios (enviado_en) VALUES (?)")
      .bind(new Date().toISOString())
      .run();
    var miTurno = reserva.meta.last_row_id;
    if (miTurno > MAX_MENSAJES) {
      return;
    }

    var citas = await env.DB.prepare(
      "SELECT titulo, fecha_hora, lugar FROM citas_prueba ORDER BY fecha_hora"
    ).all();
    var lista = citas.results || [];
    var ahora = ahoraMadrid();
    var proxima = lista.find(function (c) { return c.fecha_hora >= ahora; }) || lista[0];

    var texto = "Prueba del acompañante (datos de mentira).\n";
    texto += "Tienes " + lista.length + " citas de prueba guardadas en la nube.\n";
    if (proxima) {
      texto += "La próxima: " + proxima.titulo + ", " + formatoBonito(proxima.fecha_hora);
      if (proxima.lugar) {
        texto += ", en " + proxima.lugar;
      }
      texto += ".\n";
    }
    texto += "Mensaje " + miTurno + " de " + MAX_MENSAJES + ".";

    var respuesta = await fetch("https://api.telegram.org/bot" + env.TELEGRAM_TOKEN + "/sendMessage", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text: texto }),
    });
    if (!respuesta.ok) {
      throw new Error("Telegram ha respondido con error " + respuesta.status);
    }
  },
};
