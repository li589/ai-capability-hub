---
name: procurement-kit
description: Pass the procurement gate quickly — fill the vendor form, attach the standard legal/financial supports (Cámara y Comercio, RUT, certificados), and propose payment terms + SLAs that match Arkangel's standards. Compartment 5 of the Arkangel sales submarine.
install_source: official
install_method: download
skill_id: official_LfJyQQ8N
enabled_at: 1787232949209
version: 1.0.0
name_zh: 采购工具包
---

# Procurement Kit

Compartment 5 of the Arkangel sales submarine. Procurement won't grow your deal — but it can kill it by stalling. The job here: give compras everything they need on day one so they have no reason to delay.

## When to Use

- DMs validated the bracket (compartment 4 closed) and the deal moves to procurement / compras.
- The owner says "responde el vendor form de X" or "qué necesita compras de nosotros".
- Procurement sent a vendor onboarding template and we need to fill it.

**Do not use** before compartment 4 closed (a vendor form filled without a bracket validated will trigger requote loops), or for legal documents — those are `legal-kit`.

## Inputs

- **Required:** vendor form recibido (PDF / Word / portal), nombre legal del prospecto.
- **Optional:** condiciones de pago preferidas del cliente, lista de referencias autorizadas, anteriores vendor forms del mismo cliente.

## Procedure

1. **Read the vendor form completely.** Map every required field to one of:
   - Datos de identificación legal Arkangel (NIT, razón social, dirección, representante legal).
   - Soportes documentales (Cámara y Comercio, RUT, estados financieros, certificados ISO/SOC2).
   - Datos comerciales (términos pago, SLA, anticipo, monedas aceptadas).
   - Referencias de clientes.
   - Cuestionarios anti-corrupción / OFAC / lista Clinton.
   - Otros (datos bancarios, certificación calidad, etc).

2. **Fill the legal/identification block.**
   - Razón social: ARKANGEL AI S.A.S. (o entidad correspondiente según jurisdicción del cliente).
   - NIT, dirección, representante legal — del registro vigente.
   - Adjuntar Cámara y Comercio + RUT vigentes (< 30 días si el cliente lo exige).

3. **Attach financial supports.**
   - Estados financieros del último año fiscal si lo piden.
   - Certificación bancaria si lo piden.
   - Si los pide pero no aplican (etapa temprana), explica con una línea — no inventes.

4. **Attach quality / security certificates.**
   - ISO27001 status (en proceso / certificado / no aplica).
   - SOC2 status.
   - Pentest evidencia (Hackmetrix Feb 2026 — referencia, no PDF completo en este compartimento; el detalle va en `security-kit`).

5. **Propose términos comerciales.**
   - Pago: 30 días neto preferido, 45 negociable, 60 con descuento. Sin anticipos en deals nuevos enterprise (riesgo de cobro).
   - Moneda: COP por defecto; USD si el contrato es internacional.
   - SLA básico: 99,5 % uptime, soporte L1 en 4 horas hábiles, L2 en 24 horas. SLAs más estrictos van a `legal-kit`.
   - Cláusula de revisión anual de precio (CPI o renegociación).

6. **References de clientes.**
   - Mínimo 2, máximo 4. Sólo con permiso explícito del referente.
   - Indica sector + tamaño + caso similar al deal actual.
   - Si no hay referencias del sector exacto, propón referencia adyacente y explica el paralelo.

7. **Cuestionarios anti-corrupción y similares.**
   - Lista Clinton / OFAC: respuesta estándar Arkangel.
   - Beneficiarios reales: completa con UBO actuales.
   - Política anti-soborno: referencia al código de conducta interno.

8. **Output structure.**

   ```markdown
   # Procurement Kit — <Empresa> · <Date>

   ## Vendor form respondido
   <campo a campo, con valor o referencia a anexo>

   ## Anexos preparados
   - Cámara y Comercio (vigente al <fecha>)
   - RUT
   - Estados financieros <año>
   - Certificación bancaria
   - SOC2 / ISO27001 status
   - Pentest summary (Hackmetrix <fecha>)

   ## Términos comerciales propuestos
   - Pago: <plazo>
   - Moneda: <COP / USD>
   - SLA: <%, soporte L1, L2>
   - Revisión anual: <CPI o renegociación>

   ## Referencias autorizadas
   - <cliente, sector, contacto, paralelo con el deal actual>

   ## Cuestionarios complementarios
   - Anti-corrupción / OFAC: respondido
   - UBO: respondido
   - Otros: <lista>

   ## Gaps abiertos
   - <campos del vendor form que no podemos responder hoy + plan>
   ```

9. **Update Attio.**
   - Notar fecha de envío del kit.
   - `pipeline_stage = 6.legal` cuando procurement confirme que está OK.

## Pitfalls

- **Síntoma:** se envía el vendor form a medias para "ganar tiempo". **Causa:** prisa del champion. **Fix:** procurement va a regresar con preguntas extra — el tiempo no se gana, se pierde. Mejor 2 días para llenar bien que 2 semanas de ping-pong.
- **Síntoma:** se inventa un certificado ISO27001 que está "en proceso". **Causa:** miedo a perder el deal. **Fix:** se dice exactamente el estado real + plan + fecha objetivo. Inventar mata deals enterprise.
- **Síntoma:** referencias entregadas sin avisar al referente. **Causa:** ahorro de fricción interna. **Fix:** **siempre** pedir permiso antes; un referente sorprendido daña la relación y a veces el deal.
- **Síntoma:** términos de pago aceptados a 90+ días sin escalación. **Causa:** comercial no quiso negociar. **Fix:** > 60 días requiere aprobación CFO Arkangel; el skill marca el campo como "escalación requerida" y no lo cierra solo.

## Verification

- Cada campo del vendor form tiene respuesta o un anexo referenciado, no campos vacíos.
- Todos los certificados adjuntos están vigentes (< 30 días si el cliente lo exige).
- Las referencias tienen permiso explícito documentado.
- Los términos de pago propuestos están dentro de la política Arkangel o tienen escalación marcada.

## References

- [`sales-pipeline`](../sales-pipeline/) — submarino completo.
- [`decision-maker-kit`](../decision-maker-kit/) — compartimento previo, debe estar cerrado.
- [`legal-kit`](../legal-kit/) — siguiente compartimento.
- [`security-kit`](../security-kit/) — el detalle de seguridad va separado, no se incluye aquí.
