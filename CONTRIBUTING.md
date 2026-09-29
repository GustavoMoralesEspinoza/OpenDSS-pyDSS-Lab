# Guía de Contribución a OpenDSS-pyDSS-Lab 🤝

¡Gracias por su interés en contribuir a **OpenDSS-pyDSS-Lab**! Este proyecto es un recurso educativo abierto diseñado para la enseñanza e investigación en sistemas de distribución eléctrica y recursos energéticos distribuidos (DER).

---

## 🧭 ¿Cómo puedo contribuir?

Aceptamos contribuciones en diversas áreas:
1. **Nuevos Circuitos de Prueba:** Modelos OpenDSS de alimentadores reales o de prueba estándar (ej. IEEE 13-Bus, IEEE 34-Bus, IEEE 123-Bus, redes europeas CIGRE).
2. **Nuevas Funciones de Control:** Implementaciones de algoritmos de control coordinado de inversores, gestión de carga de vehículos eléctricos (V2G/G2V), o regulación de tomas de transformadores bajo carga (OLTC).
3. **Traducciones:** Traducción de cuadernos a otros idiomas (portugués, inglés, francés, etc.).
4. **Corrección de Errores y Documentación:** Corrección tipográfica, mejoras en fórmulas LaTeX o clarificación de explicaciones conceptuales.

---

## 📋 Flujo de Trabajo para Contribuir

1. **Haga un Fork del Repositorio:**
   Cree una copia personal del proyecto en su cuenta de GitHub.

2. **Clone su Fork Localmente:**
   ```bash
   git clone https://github.com/TU-USUARIO/OpenDSS-pyDSS-Lab.git
   cd OpenDSS-pyDSS-Lab
   ```

3. **Cree una Rama Descriptiva:**
   ```bash
   git checkout -b feature/nuevo-control-inversor
   ```

4. **Prepare su Entorno de Desarrollo:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # o .\venv\Scripts\activate en Windows
   pip install -r requirements.txt
   ```

5. **Asegure la Calidad del Código:**
   - Todo cuaderno modificado debe compilar y ejecutar de principio a fin sin errores.
   - Las celdas de markdown deben utilizar KaTeX formal para ecuaciones matemáticas.
   - Las variables y nombres de funciones deben seguir las convenciones de PEP 8.

6. **Haga Commit y Push:**
   ```bash
   git commit -m "feat: implementar control de factor de potencia dinámico en Módulo 5"
   git push origin feature/nuevo-control-inversor
   ```

7. **Abra un Pull Request (PR):**
   Describa claramente el objetivo de su cambio, las pruebas realizadas y los resultados obtenidos.

---

## 📜 Código de Conducta
Mantenemos un entorno acogedor, inclusivo y respetuoso para estudiantes, docentes e investigadores de todo el mundo.
