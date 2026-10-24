import React from "react";

export default function HandbookView() {
  return (
    <section className="tab-content" style={{ display: "block" }}>
      <div className="page-heading">
        <h2>Ficha técnica: trips en gulupa</h2>
        <p>Especies, fases del ciclo biológico y daño económico en fruta de exportación.</p>
      </div>

      <div className="recs-card">
        <div className="rec-group">
          <div className="rec-group-title">Especies principales en Colombia y la región andina</div>
          <ul className="rec-list">
            <li>
              <b>Frankliniella occidentalis:</b> Trips de las flores. Insecto alargado, de color amarillento a pardo oscuro, alas estrechas con flecos largos plumosos. Muy polífago y transmisor de tospovirus. Ataca con severidad botones y frutos recién fecundados.
            </li>
            <li>
              <b>Frankliniella panamensis:</b> Presente con frecuencia en inflorescencias y zarcillos de pasifloráceas.
            </li>
            <li>
              <b>Thrips tabaci:</b> Color amarillo pálido a marrón claro, presente en hojas tiernas y botones durante temporadas secas.
            </li>
          </ul>
        </div>

        <div className="rec-group">
          <div className="rec-group-title">Fases del ciclo biológico (4 fases reales)</div>
          <ul className="rec-list">
            <li>
              <b>Huevo:</b> Ovalado y translúcido, insertado microscópicamente en hojas, botones florales o frutos tiernos.
            </li>
            <li>
              <b>Larva (Ninfa):</b> Único estadio larval/ninfal activo, sin alas; translúcido a amarillo o anaranjado. Es la fase voraz que raspa la epidermis vegetal. No se divide en Ninfa I y Ninfa II.
            </li>
            <li>
              <b>Pupa (Prepupa):</b> Estadio de reposo en suelo, grietas o espalderas; no se alimenta y presenta esbozos alares.
            </li>
            <li>
              <b>Adulto:</b> Fase reproductora con alas plumosas franjeadas, alta movilidad, dispersión y oviposición en flores.
            </li>
          </ul>
        </div>

        <div className="rec-group">
          <div className="rec-group-title">Síntomas y daño económico en fruto</div>
          <ul className="rec-list">
            <li>
              <b>Cacarizado o roña:</b> Ocurre cuando las larvas (ninfas) raspan la cáscara del fruto recién cuajado (&lt; 3 cm). Al crecer el fruto, las heridas cicatrizan con tejido suberoso pardo o plateado. Lesiones &gt; 1 cm² descartan el fruto de cajas de exportación directa a Europa (GlobalG.A.P.).
            </li>
            <li>
              <b>Aborto floral:</b> La alimentación en nectarios, sépalos y pistilos durante la antesis provoca caída masiva de botones florales.
            </li>
            <li>
              <b>Deformación de brotes:</b> Hojas tiernas encrespadas con clorosis marginal, punteado plateado y excremento negro fecal.
            </li>
          </ul>
        </div>

        <div className="rec-group">
          <div className="rec-group-title">Dinámica poblacional y temperatura</div>
          <ul className="rec-list">
            <li>
              A 18 °C el ciclo completo de huevo a adulto tarda aproximadamente 28 a 32 días.
            </li>
            <li>
              A 24–26 °C el ciclo se acelera drásticamente a 12–14 días, multiplicando la población en pocas semanas.
            </li>
            <li>
              Las trampas cromotrópicas adhesivas <b>AZULES (~460 nm)</b> son las más atractivas para *Frankliniella occidentalis* y permiten detección temprana antes de que aparezcan cicatrices en los frutos.
            </li>
          </ul>
        </div>
      </div>
    </section>
  );
}
