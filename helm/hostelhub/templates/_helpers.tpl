{{- define "hostelhub.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "hostelhub.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else if contains (include "hostelhub.name" .) .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name (include "hostelhub.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{- define "hostelhub.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "hostelhub.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: hostelhub
{{- end }}

{{/* Selector labels for one component: include "hostelhub.selector" (dict "ctx" . "component" "backend") */}}
{{- define "hostelhub.selector" -}}
app.kubernetes.io/name: {{ include "hostelhub.name" .ctx }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{- define "hostelhub.backendName" -}}{{ include "hostelhub.fullname" . }}-backend{{- end }}
{{- define "hostelhub.frontendName" -}}{{ include "hostelhub.fullname" . }}-frontend{{- end }}
{{- define "hostelhub.postgresName" -}}{{ include "hostelhub.fullname" . }}-postgres{{- end }}
{{- define "hostelhub.secretName" -}}{{ include "hostelhub.fullname" . }}-db{{- end }}

{{- define "hostelhub.databaseUrl" -}}
{{- if .Values.postgres.enabled -}}
postgresql+psycopg://{{ .Values.postgres.username }}:{{ .Values.postgres.password | urlquery }}@{{ include "hostelhub.postgresName" . }}:5432/{{ .Values.postgres.database }}
{{- else -}}
{{- required "externalDatabaseUrl is required when postgres.enabled=false" .Values.externalDatabaseUrl -}}
{{- end -}}
{{- end }}
