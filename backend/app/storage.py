import json,os,sqlite3
from datetime import datetime,timezone
from pathlib import Path
from .demo import DEMO_TEMPLATES
from .models import ComponentTemplate,ComponentTemplateInput,Project,ProjectInput

class Storage:
    def __init__(self,path=None):
        self.path=Path(path or os.getenv("WIRING_DB_PATH") or Path(__file__).parents[1]/"wiring.db")
        self.path.parent.mkdir(parents=True,exist_ok=True);self.initialize()
    def connect(self):
        db=sqlite3.connect(self.path);db.row_factory=sqlite3.Row;db.execute("PRAGMA foreign_keys=ON");return db
    def initialize(self):
        with self.connect() as db:
            db.executescript("CREATE TABLE IF NOT EXISTS component_templates(id TEXT PRIMARY KEY,body TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,name TEXT NOT NULL,body TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects(updated_at DESC);")
            if db.execute("SELECT COUNT(*) FROM component_templates").fetchone()[0]==0:
                for template in DEMO_TEMPLATES:self.create_template(template,db)
            db.execute("PRAGMA optimize")
    def list_templates(self):
        with self.connect() as db:return [ComponentTemplate.model_validate_json(row[0]) for row in db.execute("SELECT body FROM component_templates ORDER BY id")]
    def get_template(self,template_id):
        with self.connect() as db:row=db.execute("SELECT body FROM component_templates WHERE id=?",(template_id,)).fetchone()
        return ComponentTemplate.model_validate_json(row[0]) if row else None
    def create_template(self,value,db=None):
        now=datetime.now(timezone.utc);record=ComponentTemplate(**value.model_dump(),created_at=now,updated_at=now);own=db is None;cx=db or self.connect()
        try:
            cx.execute("INSERT INTO component_templates VALUES(?,?,?,?)",(record.id,record.model_dump_json(),now.isoformat(),now.isoformat()))
            if own:cx.commit()
        finally:
            if own:cx.close()
        return record
    def update_template(self,template_id,value):
        old=self.get_template(template_id)
        if not old:return None
        now=datetime.now(timezone.utc);data=value.model_dump();data["id"]=template_id;record=ComponentTemplate(**data,created_at=old.created_at,updated_at=now)
        with self.connect() as db:db.execute("UPDATE component_templates SET body=?,updated_at=? WHERE id=?",(record.model_dump_json(),now.isoformat(),template_id))
        return record
    def delete_template(self,template_id):
        with self.connect() as db:
            projects=[Project.model_validate_json(row[0]) for row in db.execute("SELECT body FROM projects")]
            if any(i.template_id==template_id for p in projects for i in p.instances):raise ValueError("Template is used by a project")
            return db.execute("DELETE FROM component_templates WHERE id=?",(template_id,)).rowcount>0
    def list_projects(self):
        with self.connect() as db:return [Project.model_validate_json(row[0]) for row in db.execute("SELECT body FROM projects ORDER BY updated_at DESC")]
    def get_project(self,project_id):
        with self.connect() as db:row=db.execute("SELECT body FROM projects WHERE id=?",(project_id,)).fetchone()
        return Project.model_validate_json(row[0]) if row else None
    def create_project(self,value):
        record=Project(**value.model_dump())
        with self.connect() as db:db.execute("INSERT INTO projects VALUES(?,?,?,?,?)",(record.id,record.name,record.model_dump_json(by_alias=True),record.created_at.isoformat(),record.updated_at.isoformat()))
        return record
    def update_project(self,project_id,value):
        old=self.get_project(project_id)
        if not old:return None
        record=Project(id=project_id,created_at=old.created_at,updated_at=datetime.now(timezone.utc),**value.model_dump())
        with self.connect() as db:db.execute("UPDATE projects SET name=?,body=?,updated_at=? WHERE id=?",(record.name,record.model_dump_json(by_alias=True),record.updated_at.isoformat(),project_id))
        return record
    def delete_project(self,project_id):
        with self.connect() as db:return db.execute("DELETE FROM projects WHERE id=?",(project_id,)).rowcount>0
