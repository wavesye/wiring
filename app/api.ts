import type {Project,ProjectInput,Rules,Template,Validation} from "./types";
const base=(process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000/api").replace(/\/$/,"");
async function request<T>(path:string,init?:RequestInit):Promise<T>{
 const response=await fetch(`${base}${path}`,{...init,headers:{"Content-Type":"application/json",...init?.headers}});
 if(!response.ok){let message=`Request failed (${response.status})`;try{const body=await response.json();message=body.detail?.message||body.detail||message}catch{message=`Request failed (${response.status})`}throw new Error(typeof message==="string"?message:JSON.stringify(message))}
 return response.status===204?undefined as T:response.json();
}
export const api={
 templates:()=>request<Template[]>("/component-templates"),rules:()=>request<Rules>("/rules"),projects:()=>request<Project[]>("/projects"),
 createTemplate:(value:Template)=>request<Template>("/component-templates",{method:"POST",body:JSON.stringify(value)}),
 updateTemplate:(id:string,value:Template)=>request<Template>(`/component-templates/${id}`,{method:"PUT",body:JSON.stringify(value)}),
 deleteTemplate:(id:string)=>request<void>(`/component-templates/${id}`,{method:"DELETE"}),
 importTemplate:(value:Template)=>request<Template>("/component-templates/import",{method:"POST",body:JSON.stringify(value)}),
 getProject:(id:string)=>request<Project>(`/projects/${id}`),createProject:(value:ProjectInput)=>request<Project>("/projects",{method:"POST",body:JSON.stringify(value)}),
 saveProject:(id:string,value:ProjectInput)=>request<Project>(`/projects/${id}`,{method:"PUT",body:JSON.stringify(value)}),deleteProject:(id:string)=>request<void>(`/projects/${id}`,{method:"DELETE"}),
 validate:(id:string)=>request<Validation>(`/projects/${id}/validate`,{method:"POST"}),download:(id:string,format:"csv"|"excel")=>window.open(`${base}/projects/${id}/export/${format}`,"_blank")
};
