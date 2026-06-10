<div align="center">

<a href="README.md">简体中文</a> · <a href="README_EN.md">English</a> · <a href="README_JA.md">日本語</a> · <a href="README_KO.md">한국어</a> · <a href="README_ES.md">Español</a>

# 🔬 x-account-teardown

**Una "autopsia de crecimiento" a nivel de datos para cualquier cuenta de X (Twitter)**

Dale un `@handle` → exporta todos los tweets → reconstruye exactamente cómo creció la cuenta desde cero

</div>

---

No es otro scraper de tweets más. Responde a una pregunta mucho más valiosa:

> **¿Cómo creció realmente esta gran cuenta desde cero? ¿Cuáles fueron su contenido, su cadencia y sus tácticas, y cómo las copio?**

Despliega todo el historial de tweets de una cuenta en la línea de tiempo y aplica ingeniería inversa a su curva de crecimiento: **letargo → punto de inflexión → pilares de contenido → cadencia de publicación → estrategia de respuestas → fórmulas de ganchos virales → curva de crecimiento**. Al final entrega un informe listo para usar, del tipo "copia los deberes".

## 📈 Ejemplo (un creador real del nicho de IA que llegó a 20 mil seguidores en 14 meses)

Consulta el informe de ejemplo completo en [`assets/sample/REPORT.md`](assets/sample/REPORT.md). De un vistazo: inactivo durante todo 2025, luego un arranque repentino en 2026-01 (62 originales + 420 respuestas en un solo mes), con los "me gusta" promedio subiendo de forma sostenida después.

El informe te muestra:
- **Línea de tiempo del crecimiento** — 10 meses inactivo tras registrarse, luego apostó todo
- **Pilares de contenido** — `vídeo / Claude / Codex / herramientas / modelos / aprendizaje`, un carril puramente de herramientas de IA
- **Estrategia de respuestas** — 5× más respuestas que originales, arranque en frío acampando en las secciones de respuestas de las cuentas grandes (con un Top-20 de objetivos)
- **Fórmulas de ganchos virales** — entre los 60 mejores posts, "primera persona/experiencia propia" ×31, los ganchos de "tutorial paso a paso" y "gratis/gratuito" dominan
- **Lista para copiar** — 5 conclusiones directamente accionables

## ✨ Por qué es diferente

| | Scraper típico | x-account-teardown |
|---|---|---|
| Autenticación | Copias un token a mano desde DevTools | **Extrae cookies automáticamente de tu Chrome con sesión iniciada** (incluye httpOnly, cero configuración) |
| Límite de 3200 | Choca contra el muro, pierde los tweets antiguos | **La búsqueda por ventanas de fechas sortea el límite**, hasta el tweet n.º 1 |
| Salida | Un montón de JSON | **Informe de autopsia + gráfico de curva de crecimiento + lista para copiar** |
| Insight | Ninguno | Detecta automáticamente el punto de inflexión, la pendiente de crecimiento, las fórmulas de ganchos y los objetivos de respuesta |

## 🚀 Uso

Esto es una Skill de [Claude Code](https://claude.com/claude-code). Solo dile a Claude:

```
Analiza cómo creció la cuenta de @naval
```

Claude ejecuta todo el pipeline adquirir → analizar → informar y te da una lectura en lenguaje claro.

### Ejecútalo manualmente

```bash
# 1. Instalar (Python 3.10+)
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 2. Inicia Chrome con un puerto de depuración, con sesión en x.com (para la extracción automática de cookies)
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# 3. Pipeline
.venv/bin/python scripts/acquire.py naval --out out/naval_export
.venv/bin/python scripts/analyze.py out/naval_export
.venv/bin/python scripts/report.py out/naval_export/analysis.json --out-dir out/naval_report
```

¿Sin Chrome con puerto de depuración? Usa `--cookies 'auth_token=...; ct0=...'` o la variable de entorno `X_COOKIES`.

## 🧩 Cómo funciona

```
acquire.py   twscrape + extracción automática de cookies + autodetección de proxy + sorteo del 3200 + filtro por autor
   ↓ all_posts.json / profile.json
analyze.py   detección del punto de inflexión / crecimiento mensual / pilares de contenido (jieba) / cadencia / estrategia de respuestas / ganchos / virales
   ↓ analysis.json
report.py    informe de autopsia en Markdown + SVG de curva de crecimiento hecho en Python puro
   ↓ REPORT.md / growth.svg
```

Consulta [`references/methodology.md`](references/methodology.md) para el marco de análisis de crecimiento y los detalles técnicos.

## ⚠️ Notas

- Los datos provienen de los endpoints públicos de X: solo tweets públicos e interacción. Las curvas de seguidores no son públicas; esta herramienta usa los "me gusta"/visualizaciones promedio a lo largo del tiempo como indicador indirecto de crecimiento.
- Los tweets eliminados / solo para seguidores no se pueden recuperar.
- En algunas regiones puede que necesites un proxy para llegar a x.com (el script reutiliza tu proxy del sistema / sondea el 7890 local).
- **⚠️ Usa una cuenta secundaria dedicada, no la principal**: la herramienta actúa con la identidad de la cuenta que tengas iniciada en Chrome, así que cualquier riesgo antiabuso recae en esa cuenta. Solo el scraping masivo de alta frecuencia es arriesgado; extraer unos pocos miles de tweets de vez en cuando está bien.
- Solo para investigación. No hagas scraping masivo repetido de la misma cuenta.

## ⭐ Historial de estrellas

[![Star History Chart](https://api.star-history.com/svg?repos=ai-martin-lau/x-account-teardown&type=Date)](https://star-history.com/#ai-martin-lau/x-account-teardown&Date)

## 📄 Licencia

MIT
