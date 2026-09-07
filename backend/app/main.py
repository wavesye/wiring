from io import BytesIO, StringIO
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from .engine import RuleEngine, export_rows
from .models import Project, ValidationResult

app = FastAPI(title="Visual Wiring Definition API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health(): return {"status": "ok"}

@app.post("/api/v1/validate", response_model=ValidationResult)
def validate(project: Project): return RuleEngine(project).validate()

def validated_rows(project: Project):
    result = RuleEngine(project).validate()
    if not result.valid:
        raise HTTPException(422, detail=result.model_dump())
    return export_rows(project)

@app.post("/api/v1/export/csv")
def export_csv(project: Project):
    out = StringIO(); pd.DataFrame(validated_rows(project)).to_csv(out, index=False)
    return Response(out.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=wiring-definition.csv"})

@app.post("/api/v1/export/excel")
def export_excel(project: Project):
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        pd.DataFrame(validated_rows(project)).to_excel(writer, sheet_name="Wiring Definition", index=False)
        ws = writer.book["Wiring Definition"]; ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
        for cell in ws[1]: cell.font = cell.font.copy(bold=True); cell.fill = cell.fill.copy(fill_type="solid", fgColor="E9E3FF")
        for column in ws.columns: ws.column_dimensions[column[0].column_letter].width = max(14, min(32, max(len(str(cell.value or "")) for cell in column) + 2))
    return Response(out.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=wiring-definition.xlsx"})
