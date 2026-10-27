/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const componente: DefineComponent<Record<string, never>, Record<string, never>, unknown>
  export default componente
}
