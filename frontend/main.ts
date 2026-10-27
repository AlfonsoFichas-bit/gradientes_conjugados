import './tailwind.css'
import './app.css'

import { createInertiaApp } from '@inertiajs/vue3'
import { createApp, h } from 'vue'
import type { DefineComponent } from 'vue'

createInertiaApp({
  title: (title) => (title ? `${title} · Simulador presupuestario` : 'Simulador presupuestario | USIE'),
  resolve: (name) => {
    const paginas = import.meta.glob('./pages/**/*.vue', { eager: true }) as Record<
      string,
      { default: DefineComponent }
    >
    const pagina = paginas[`./pages/${name}.vue`]
    if (!pagina) {
      throw new Error(`Página de Inertia no encontrada: ${name}`)
    }
    return pagina.default
  },
  setup({ el, App, props, plugin }) {
    createApp({ render: () => h(App, props) }).use(plugin).mount(el)
  },
  http: {
    xsrfCookieName: 'csrftoken',
    xsrfHeaderName: 'X-CSRFToken',
  },
})
