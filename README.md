# Componentes Disponibles para RCU (OSB 12c)

Puedes especificar estos componentes en `rcu.component` (separados por comas):

| Componente | Descripción |
|------------|-----------------------------|
| SOAINFRA  | Infraestructura SOA |
| ESS       | Enterprise Scheduler |
| MDS       | Metadata Services |
| ORASDPM   | Service Data Performance Monitor |
| ORASDPS   | Service Data Performance Server |
| ORASDPA   | Service Data Performance Analytics |
| OPSS      | Security Services |
| BAM       | Business Activity Monitoring |
| UCSUMS    | User Messaging Service |


# Templates Principales para OSB 12c

**Ruta base:** `$MW_HOME/oracle_common/common/templates/wls/` o `$MW_HOME/osb/common/templates/wls/`

| Template         | Ruta Completa                                         | Descripción |
|-----------------|------------------------------------------------------|-------------|
| osb.jar        | `$MW_HOME/osb/common/templates/wls/osb.jar`          | Dominio puro OSB (solo Oracle Service Bus). Ideal para integración de servicios. |
| osb_soa.jar    | `$MW_HOME/osb/common/templates/wls/osb_soa.jar`      | Dominio combinado OSB + SOA Suite (BPEL, BPM). Para procesos + integración. |
| osb_soa_bpm.jar| `$MW_HOME/osb/common/templates/wls/osb_soa_bpm.jar`  | Incluye OSB + SOA + BPM (Business Process Management). |
| soa.jar        | `$MW_HOME/soa/common/templates/wls/soa.jar`          | Solo SOA Suite (sin OSB). Para automatización de procesos (BPEL, Human Workflow). |
| em.jar         | `$MW_HOME/em/common/templates/wls/em.jar`            | Enterprise Manager (monitoreo y administración). |
| em_osb.jar     | `$MW_HOME/em/common/templates/wls/em_osb.jar`        | EM + plugin para OSB (monitoreo específico de servicios). |
| restricted.jar | `$MW_HOME/oracle_common/common/templates/wls/restricted.jar` | Dominio mínimo (sin componentes adicionales). Lightweight. |
| adf.jar        | `$MW_HOME/oracle_common/common/templates/wls/adf.jar` | Application Development Framework (para aplicaciones personalizadas). |
| bam.jar        | `$MW_HOME/soa/common/templates/wls/bam.jar`          | Business Activity Monitoring (dashboards en tiempo real). |

---

## Templates para Componentes Adicionales  
*(Requieren licencias específicas)*  

| Template  | Ruta Completa                                         | Descripción |
|-----------|------------------------------------------------------|-------------|
| ess.jar  | `$MW_HOME/soa/common/templates/wls/ess.jar`         | Enterprise Scheduler (ejecución programada de jobs). |
| em_ess.jar | `$MW_HOME/em/common/templates/wls/em_ess.jar`      | EM + plugin para ESS (gestión de jobs desde la consola). |
| ucm.jar   | `$MW_HOME/oracle_common/common/templates/wls/ucm.jar` | Universal Content Management (gestión documental). |
