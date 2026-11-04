from acompanante.cli import main


def test_flujo_completo_en_consola(cfg, capsys):
    assert main(["iniciar"], cfg) == 0
    assert main([
        "nueva-cita", "--titulo", "Analítica", "--tipo", "analitica",
        "--fecha", "12/11/2099", "--hora", "8:30", "--lugar", "Centro de salud",
        "--preparar", "Ve en ayunas", "--preparar", "Lleva la muestra de orina",
    ], cfg) == 0
    assert main(["citas"], cfg) == 0
    salida = capsys.readouterr().out
    assert "Cita guardada" in salida
    assert "jueves 12 de noviembre a las 8:30: Analítica" in salida

    assert main(["avisos", "--ahora", "10/11/2099 10:00"], cfg) == 0
    salida = capsys.readouterr().out
    assert "1. Ve en ayunas." in salida
    assert "Avisos enviados: 1" in salida

    assert main(["avisos", "--ahora", "10/11/2099 10:05"], cfg) == 0
    assert "no toca ningún aviso" in capsys.readouterr().out


def test_fecha_mal_escrita_no_rompe(cfg, capsys):
    codigo = main(["nueva-cita", "--titulo", "X", "--fecha", "mañana", "--hora", "9:00"], cfg)
    assert codigo == 1
    assert "Escríbela así" in capsys.readouterr().out


def test_demo(cfg, capsys):
    assert main(["demo"], cfg) == 0
    salida = capsys.readouterr().out
    assert "Así te llegará el aviso 2 días antes" in salida
    assert "Pasado mañana" in salida
